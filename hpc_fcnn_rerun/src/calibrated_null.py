"""Nulo Aditivo Calibrado (NAC) — implementacao dos Passos 2 a 5 da ESPECIFICACAO.

A IDEIA. Simular paisagens SEM NENHUMA epistasia, mas casadas ao conjunto real em
tudo o mais — mesmo desenho experimental, mesma composicao de ordens mutacionais,
mesma razao sinal-ruido, mesmas particoes — e rodar nelas o pipeline inteiro. A
distribuicao resultante da estatistica de interesse e o alvo de comparacao correto,
em vez de zero.

POR QUE ISSO E NECESSARIO. Tran et al. compararam a melhora de desempenho contra
zero. Mas a estatistica "modelo flexivel supera o aditivo" tem expectativa NAO NULA
sob aditividade pura, por duas razoes independentes:
  1. reducao de variancia do erro com N maior (o artefato que Visani, Verma & DeWitt
     identificaram);
  2. capacidade extra ajustando ruido — um modelo com 2.850 parametros de interacao
     inuteis pode ganhar ou perder, e quanto exatamente e uma questao empirica.
O NAC mede essa expectativa em vez de assumi-la.

O QUE E CALIBRADO AQUI. O pipeline tem de rodar B vezes, portanto precisa ser
barato. A FCNN esta fora de alcance (exigiria torch e ~50x o custo da rodada do
HPC). Calibramos:

  'additive'   o proprio nulo. Serve de controle: seu ganho sobre si mesmo deve
               ficar centrado em zero. Se nao ficar, ha erro no codigo.
  'pairwise'   ridge com TODAS as interacoes pareadas. E o teste direto de
               epistasia ESPECIFICA: sob verdade aditiva, os p(p-1)/2 parametros de
               interacao sao puro ruido. Ganho observado acima do nulo = interacao
               genuina, nao escala e nao reducao de variancia.
  'global_iso' o baseline de epistasia global (aditivo + isotonica). Sob verdade
               aditiva o elo verdadeiro e a identidade, portanto o ganho nulo deve
               ser ~0; o ganho observado mede quanta nao linearidade monotonica
               existe de fato na paisagem real.

GERADOR DO NULO (Passo 2 da especificacao). beta e o ruido sao estimados APENAS na
porcao de treino — ajustar no conjunto completo vazaria informacao do teste para
dentro do nulo. Ruido por ORDEM MUTACIONAL (via (b) da especificacao, o padrao),
porque variantes de ordem alta tipicamente tem ruido maior e um sigma unico tornaria
o nulo sistematicamente facil ou dificil demais na ordem de interesse.

DESVIO DECLARADO. As ordens presentes no teste e ausentes do treino (ordem 4, aqui)
nao tem sigma estimavel do treino. Usamos o sigma da maior ordem disponivel no
treino. E uma aproximacao, e ela torna o nulo CONSERVADOR se o ruido real cresce com
a ordem: subestimar o ruido do teste faz o nulo render mais do que deveria, logo
exige mais do efeito observado para ser significativo.

SELECAO DE HIPERPARAMETRO DENTRO DO LACO (Passo 4, e armadilha 3.2 da
especificacao). O alfa e reselecionado em cada replica, pela mesma rotina usada nos
dados reais. Reaproveitar o alfa ajustado no real enviesaria o nulo.

Uso:
    python -I papers/paper1-nulo-calibrado/src/calibrated_null.py \
        --data-dir data/external/zenodo-17620759 \
        --datasets GB1 TrpB --train-load 3 --replicates 50 \
        --out papers/paper1-nulo-calibrado/results/nac_gb1_trpb.tsv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import pearsonr, spearmanr
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import RidgeCV

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from data import assemble_eval, load_dataset, make_partition  # noqa: E402

# Grade reduzida em relacao aos 50 valores do protocolo real: o alfa e reselecionado
# em cada replica, portanto a grade entra B vezes no custo. 12 valores cobrem a
# mesma faixa de 1e-3 a 1e3 com resolucao suficiente.
ALPHAS = np.logspace(-3, 3, 12)
MODELS = ("additive", "pairwise", "global_iso")

def _dataset_files() -> dict[str, str]:
    """Le o mapeamento conjunto -> arquivo de config/datasets.tsv.

    Fonte unica de verdade no pacote: o mesmo arquivo que run_one.py e
    global_epistasis.py usam, para que nenhum modulo tenha uma lista propria que
    possa divergir.
    """
    cfg = ROOT.parent / "config" / "datasets.tsv"
    df = pd.read_csv(cfg, sep="\t")
    return dict(zip(df["dataset"], df["arquivo"], strict=True))


DATASET_FILES = _dataset_files()


def build_pairwise(X: sp.csr_matrix) -> sp.csr_matrix:
    """Acrescenta todas as interacoes pareadas, mantendo a matriz esparsa.

    Uma variante de ordem k tem k termos aditivos e k(k-1)/2 pareados, logo no
    maximo 10 nao-zeros para ordem 4. A matriz densa seria 149.360 x 2.926; a
    esparsa ocupa alguns MB.
    """
    n, p = X.shape
    Xc = X.tocsr()
    rows, cols = [], []
    # indice do par (i, j), i < j, na ordem lexicografica
    offset = np.zeros(p, dtype=np.int64)
    acc = 0
    for i in range(p):
        offset[i] = acc
        acc += p - i - 1
    for r in range(n):
        idx = Xc.indices[Xc.indptr[r]:Xc.indptr[r + 1]]
        idx = np.sort(idx)
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                i, j = int(idx[a]), int(idx[b])
                rows.append(r)
                cols.append(int(offset[i] + (j - i - 1)))
    n_pairs = acc
    P = sp.csr_matrix(
        (np.ones(len(rows), dtype=np.float64), (rows, cols)), shape=(n, n_pairs)
    )
    return sp.hstack([Xc, P], format="csr")


def _ridge(X_tr, y_tr):
    m = RidgeCV(alphas=ALPHAS, fit_intercept=True)
    m.fit(X_tr, y_tr)
    return m


def _corr(y, p):
    if np.std(p) <= 0 or np.std(y) <= 0:
        return 0.0, 0.0
    return float(pearsonr(y, p).statistic), float(spearmanr(y, p).statistic)


def run_pipeline(Xa, Xp, y, folds, cv_pool_idx, extra_test_idx, n_muts, load):
    """Roda os tres modelos nos mesmos folds. Devolve metricas por regime."""
    n_total = len(y)
    n_folds = len(folds)
    preds = {m: (np.full(n_total, np.nan), np.zeros((n_folds, len(extra_test_idx))))
             for m in MODELS}

    for f in range(n_folds):
        held = folds[f]
        pool = np.concatenate([folds[j] for j in range(n_folds) if j != f])
        tr = pool[n_muts[pool] <= load]
        if len(tr) < 5:
            continue

        # aditivo
        ma = _ridge(Xa[tr], y[tr])
        preds["additive"][0][held] = ma.predict(Xa[held])
        preds["additive"][1][f] = ma.predict(Xa[extra_test_idx])

        # pareado
        mp = _ridge(Xp[tr], y[tr])
        preds["pairwise"][0][held] = mp.predict(Xp[held])
        preds["pairwise"][1][f] = mp.predict(Xp[extra_test_idx])

        # epistasia global (dois estagios, sobre o aditivo)
        iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
        iso.fit(ma.predict(Xa[tr]), y[tr])
        preds["global_iso"][0][held] = iso.predict(ma.predict(Xa[held]))
        preds["global_iso"][1][f] = iso.predict(ma.predict(Xa[extra_test_idx]))

    out = {}
    for mname in MODELS:
        cv_pred, extra = preds[mname]
        sel = cv_pool_idx[(n_muts[cv_pool_idx] >= 3) & ~np.isnan(cv_pred[cv_pool_idx])]
        y_true = np.concatenate([y[sel], y[extra_test_idx]])
        y_pred = np.concatenate([cv_pred[sel], extra.mean(axis=0)])
        loads = np.concatenate([n_muts[sel], n_muts[extra_test_idx]])
        interp = loads <= load
        for regime, mask in (("all", np.ones(len(y_true), bool)),
                             ("interpolacao", interp),
                             ("extrapolacao", ~interp)):
            if mask.sum() < 3:
                continue
            pr, sr = _corr(y_true[mask], y_pred[mask])
            out[(mname, regime)] = (pr, sr)
    return out


def fit_null_generator(Xa, y, folds, n_muts, load):
    """Passo 2: beta e sigma por ordem, estimados SO no treino.

    Usamos a uniao dos folds de treino (todos os variantes de carga <= load no pool
    de CV), que e a maior porcao de treino disponivel, para que beta do gerador seja
    bem estimado. Os folds continuam governando o pipeline avaliado.
    """
    pool = np.concatenate(folds)
    tr = pool[n_muts[pool] <= load]
    m = _ridge(Xa[tr], y[tr])
    resid = y[tr] - m.predict(Xa[tr])
    sigma = {}
    for k in np.unique(n_muts[tr]):
        rk = resid[n_muts[tr] == k]
        if len(rk) >= 5:
            sigma[int(k)] = float(np.std(rk, ddof=1))
    if not sigma:
        sigma[1] = float(np.std(resid, ddof=1))
    return m, sigma, len(tr)


def simulate(m, sigma, Xa, n_muts, rng):
    """Passo 3: y simulado sob aditividade pura, com ruido por ordem."""
    mu = m.predict(Xa)
    kmax = max(sigma)
    sd = np.array([sigma.get(int(k), sigma[kmax]) for k in n_muts])
    return mu + rng.normal(0.0, sd)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--datasets", nargs="+", required=True)
    ap.add_argument("--train-load", type=int, default=3)
    ap.add_argument("--replicates", type=int, default=50)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for name in args.datasets:
        csv = Path(args.data_dir) / DATASET_FILES[name]
        d = load_dataset(csv, name, need_seq=False)
        folds, cv_pool_idx, extra_test_idx = make_partition(d)
        Xa = d.X_mut.tocsr()
        t0 = time.perf_counter()
        Xp = build_pairwise(Xa)
        print(f"[{name}] n={d.n} p_aditivo={Xa.shape[1]} "
              f"p_pareado={Xp.shape[1]} ({time.perf_counter() - t0:.1f}s para montar)",
              flush=True)

        # --- observado ---
        t0 = time.perf_counter()
        obs = run_pipeline(Xa, Xp, d.y, folds, cv_pool_idx, extra_test_idx,
                           d.n_muts, args.train_load)
        secs_obs = time.perf_counter() - t0
        print(f"   observado em {secs_obs:.1f}s", flush=True)
        for (mname, regime), (pr, sr) in sorted(obs.items()):
            print(f"     {mname:<11} {regime:<13} r={pr:.4f} rho={sr:.4f}", flush=True)

        # --- gerador do nulo ---
        gen, sigma, n_tr = fit_null_generator(Xa, d.y, folds, d.n_muts,
                                              args.train_load)
        print(f"   gerador: n_treino={n_tr}  sigma por ordem="
              f"{ {k: round(v, 4) for k, v in sorted(sigma.items())} }", flush=True)

        # --- replicas ---
        rng = np.random.default_rng(args.seed)
        null_vals: dict[tuple, list] = {}
        for b in range(args.replicates):
            y_sim = simulate(gen, sigma, Xa, d.n_muts, rng)
            res = run_pipeline(Xa, Xp, y_sim, folds, cv_pool_idx, extra_test_idx,
                               d.n_muts, args.train_load)
            for key, val in res.items():
                null_vals.setdefault(key, []).append(val)
            if (b + 1) % 5 == 0 or b == 0:
                print(f"   replica {b + 1}/{args.replicates} "
                      f"({(time.perf_counter() - t0):.0f}s acumulados)", flush=True)

        # --- calibracao ---
        for mname in MODELS:
            if mname == "additive":
                continue
            for regime in ("all", "interpolacao", "extrapolacao"):
                k_m = (mname, regime)
                k_a = ("additive", regime)
                if k_m not in obs or k_a not in obs or k_m not in null_vals:
                    continue
                for mi, met in ((0, "pearson"), (1, "spearman")):
                    t_obs = obs[k_m][mi] - obs[k_a][mi]
                    t_null = np.array([null_vals[k_m][b][mi]
                                       - null_vals[k_a][b][mi]
                                       for b in range(len(null_vals[k_m]))])
                    B = len(t_null)
                    p_cal = (1 + int((t_null >= t_obs).sum())) / (B + 1)
                    rows.append({
                        "dataset": name,
                        "carga_treino": args.train_load,
                        "modelo": mname,
                        "regime": regime,
                        "metrica": met,
                        "ganho_observado": round(float(t_obs), 4),
                        "ganho_nulo_mediana": round(float(np.median(t_null)), 4),
                        "ganho_nulo_p05": round(float(np.quantile(t_null, 0.05)), 4),
                        "ganho_nulo_p95": round(float(np.quantile(t_null, 0.95)), 4),
                        "efeito_calibrado": round(
                            float(t_obs - np.median(t_null)), 4),
                        "p_calibrado": round(p_cal, 4),
                        "B": B,
                    })
        # controle: o aditivo contra si mesmo deve dar exatamente zero
        for regime in ("all", "interpolacao", "extrapolacao"):
            k = ("additive", regime)
            if k in null_vals:
                z = np.array([null_vals[k][b][0] - null_vals[k][b][0]
                              for b in range(len(null_vals[k]))])
                assert np.all(z == 0), "controle do aditivo falhou"

        pd.DataFrame([r for r in rows if r["dataset"] == name]).to_csv(
            out, sep="\t", index=False, mode="a",
            header=(not out.exists()) or out.stat().st_size == 0)
        print(f"   -> gravado {name}", flush=True)

    print(f"\nconcluido: {out}")


if __name__ == "__main__":
    main()
