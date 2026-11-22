"""Baseline de epistasia global: aditivo + transformacao monotonica aprendida.

MOTIVACAO. A reexecucao da FCNN (RESULTADOS_FCNN.md) mostrou que a vantagem da rede
sobre o ridge aditivo se concentra em Pearson e na interpolacao (-0,13, p~0,001) e
quase desaparece em Spearman (-0,02). Como Spearman e invariante a transformacao
monotonica das predicoes, isso aponta que o que a rede adquire e o FORMATO da curva
de resposta — epistasia global, um efeito de escala — e nao interacao especifica
entre mutacoes.

Este modulo testa essa hipotese diretamente, com um modelo que por construcao NAO
PODE representar interacao nenhuma:

    y ~ g( x'beta ),   g monotonica nao decrescente

Se ele recuperar a maior parte dos 0,13 de Pearson, a atribuicao do desempenho da
FCNN a "aprender epistasia" fica insustentavel.

DUAS VARIANTES.

  'global_iso'   dois estagios. Ajusta beta por ridge sobre y, depois ajusta g por
                 regressao isotonica de y sobre x'beta, so no treino. Nao ha
                 realimentacao: beta ignora a nao linearidade. Propriedade util:
                 como g e monotonica, o Spearman e essencialmente identico ao do
                 aditivo puro (difere apenas pelos empates que os patamares da
                 isotonica criam). Isola o efeito em Pearson de forma limpa.

  'global_joint' ajuste conjunto por minimizacao alternada. Repete: g <- isotonica
                 de y sobre x'beta; z <- g^-1(y) por interpolacao linear na inversa
                 da isotonica; beta <- ridge sobre z. Aqui beta MUDA, portanto o
                 Spearman tambem pode mudar. E o teste honesto da hipotese.

LIMITACAO ESTRUTURAL, E ELA E INFORMATIVA. g e aprendida apenas na faixa de x'beta
observada no treino. Variantes de teste de ordem alta caem fora dessa faixa e sao
necessariamente truncadas (clip). Registramos a fracao truncada: um modelo de
epistasia global nao consegue extrapolar a propria nao linearidade, e isso limita
quanto ele pode recuperar justamente no regime de extrapolacao.

NOTA SOBRE A ISOTONICA. E a familia monotonica mais flexivel possivel, logo propensa
a sobreajuste. Isso enviesa o teste A FAVOR de recuperar o gap, o que torna um
resultado negativo mais forte: se nem ela recupera, nenhuma familia monotonica
recupera.

Protocolo, folds e escala sao importados de hpc_fcnn_rerun/src/data.py — a mesma
implementacao que produziu os resultados da FCNN, para que as particoes coincidam
exatamente.

Uso:
    python -I papers/paper1-nulo-calibrado/src/global_epistasis.py \
        --data-dir data/external/zenodo-17620759 \
        --out papers/paper1-nulo-calibrado/results/global_epistasis.tsv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import RidgeCV

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "hpc_fcnn_rerun" / "src"))
from data import (  # noqa: E402
    TRAIN_LOADS,
    assemble_eval,
    load_dataset,
    make_partition,
)

RIDGE_ALPHAS = np.logspace(-3, 3, 50)
JOINT_ITERS = 6
JOINT_TOL = 1e-6

DATASET_FILES = {
    "AAV2 VP1": "CAPSD_AAV2S_Sinai_2021.csv",
    "GB1": "SPG1_STRSG_Wu_2016.csv",
    "IGP dehydratase": "HIS7_YEAST_Pokusaeva_2019.csv",
    "NucB": "Q65J43_BACLD_g4_Thomas_2025.csv",
    "ParD3": "F7YBW8_MESOW_Aakre_2015.csv",
    "Phototropin": "PHOT_CHLRE_Chen_2023.csv",
    "TrpB": "TRPB1_THEMA_Tm9D8_Johnston_2024.csv",
    "amacGFP": "Q8WTC7_9CNID_Somermeyer_2022.csv",
    "avGFP": "GFP_AEQVI_Sarkisyan_2016.csv",
    "cgreGFP": "D7PM05_CLYGR_Somermeyer_2022.csv",
    "ppluGFP2": "Q6WV13_9MAXI_Somermeyer_2022.csv",
    "scFv": "VH14_Li_2023.csv",
}


def _dense(X, idx):
    """Densifica um subconjunto. Usar APENAS para treino, nunca para predicao.

    Os conjuntos de treino tem no maximo ~185 MB densos (ppluGFP2, carga 3). Os de
    teste nao: Phototropin tem 165.231 variantes x 2.122 features = 2,80 GB, e a
    maquina de desenvolvimento tem 7,8 GB totais. Para predizer usamos a matriz
    esparsa direto — `predict` do sklearn aceita, via safe_sparse_dot — o que leva
    esse mesmo bloco de 2,80 GB para ~8 MB.
    """
    return np.asarray(X[idx].todense(), dtype=np.float64)


# Ordem de execucao: do mais barato ao mais caro, para que resultados uteis
# apareçam cedo e o conjunto que mais pesa (Phototropin, p=2122) fique por ultimo.
ORDEM_CUSTO = [
    "NucB", "ParD3", "GB1", "TrpB", "IGP dehydratase", "scFv",
    "AAV2 VP1", "cgreGFP", "ppluGFP2", "avGFP", "amacGFP", "Phototropin",
]


def _corr(y, p):
    if np.std(p) <= 0 or np.std(y) <= 0:
        return 0.0, 0.0
    return float(pearsonr(y, p).statistic), float(spearmanr(y, p).statistic)


def _fit_ridge(X_tr, y_tr):
    m = RidgeCV(alphas=RIDGE_ALPHAS, fit_intercept=True)
    m.fit(X_tr, y_tr)
    return m


def _iso_inverse(iso: IsotonicRegression, y: np.ndarray) -> np.ndarray:
    """g^-1(y) por interpolacao linear na inversa da isotonica.

    Em patamares de g a inversa nao e unica; np.interp devolve o primeiro ponto
    compativel, o que e uma escolha deliberada e estavel. Fora da imagem de g, o
    valor e truncado nos extremos da faixa de treino.
    """
    xs = np.asarray(iso.X_thresholds_, dtype=float)
    ys = np.asarray(iso.y_thresholds_, dtype=float)
    if len(xs) < 2:
        return np.full_like(y, xs[0] if len(xs) else 0.0)
    return np.interp(y, ys, xs)


def _frac_clipped(iso: IsotonicRegression, phi: np.ndarray) -> float:
    lo = float(np.min(iso.X_thresholds_))
    hi = float(np.max(iso.X_thresholds_))
    return float(((phi < lo) | (phi > hi)).mean())


def fit_global_iso(X_tr, y_tr):
    """Dois estagios: ridge, depois isotonica sobre o preditor linear."""
    ridge = _fit_ridge(X_tr, y_tr)
    phi_tr = ridge.predict(X_tr)
    iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
    iso.fit(phi_tr, y_tr)
    return ridge, iso


def fit_global_joint(X_tr, y_tr, n_iter: int = JOINT_ITERS):
    """Minimizacao alternada entre beta e g."""
    ridge = _fit_ridge(X_tr, y_tr)
    iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
    beta_prev = None
    n_done = 0
    for _ in range(n_iter):
        phi_tr = ridge.predict(X_tr)
        if np.std(phi_tr) <= 0:
            break
        iso.fit(phi_tr, y_tr)
        z = _iso_inverse(iso, y_tr)
        if not np.all(np.isfinite(z)) or np.std(z) <= 0:
            break
        new = _fit_ridge(X_tr, z)
        n_done += 1
        delta = (
            float(np.max(np.abs(new.coef_ - beta_prev)))
            if beta_prev is not None
            else np.inf
        )
        beta_prev = new.coef_.copy()
        ridge = new
        if delta < JOINT_TOL:
            break
    # g final, sempre reajustada ao beta final
    phi_tr = ridge.predict(X_tr)
    iso.fit(phi_tr, y_tr)
    return ridge, iso, n_done


def run_dataset(csv: Path, name: str) -> list[dict]:
    d = load_dataset(csv, name, need_seq=False)
    folds, cv_pool_idx, extra_test_idx = make_partition(d)
    n_folds = len(folds)
    print(f"[{name}] n={d.n} p={d.X_mut.shape[1]} "
          f"pool_cv={len(cv_pool_idx)} teste_extra={len(extra_test_idx)}", flush=True)

    models = ("additive", "global_iso", "global_joint")
    rows: list[dict] = []

    for load in TRAIN_LOADS:
        preds = {
            m: (np.full(d.n, np.nan), np.zeros((n_folds, len(extra_test_idx))))
            for m in models
        }
        meta = {m: {"n_train": [], "secs": 0.0, "clip": [], "iters": []}
                for m in models}

        for f in range(n_folds):
            held = folds[f]
            pool = np.concatenate([folds[j] for j in range(n_folds) if j != f])
            train_idx = pool[d.n_muts[pool] <= load]
            if len(train_idx) < 5:
                continue

            X_tr = _dense(d.X_mut, train_idx)
            y_tr = d.y[train_idx]
            # Predicao em matriz ESPARSA: ver docstring de _dense.
            X_held = d.X_mut[held]
            X_extra = d.X_mut[extra_test_idx] if len(extra_test_idx) else None

            # --- aditivo puro ---
            t0 = time.perf_counter()
            ridge = _fit_ridge(X_tr, y_tr)
            preds["additive"][0][held] = ridge.predict(X_held)
            if X_extra is not None:
                preds["additive"][1][f] = ridge.predict(X_extra)
            meta["additive"]["secs"] += time.perf_counter() - t0
            meta["additive"]["n_train"].append(len(train_idx))

            # --- epistasia global, dois estagios ---
            t0 = time.perf_counter()
            r2, iso2 = fit_global_iso(X_tr, y_tr)
            phi_held = r2.predict(X_held)
            preds["global_iso"][0][held] = iso2.predict(phi_held)
            if X_extra is not None:
                phi_extra = r2.predict(X_extra)
                preds["global_iso"][1][f] = iso2.predict(phi_extra)
                meta["global_iso"]["clip"].append(_frac_clipped(iso2, phi_extra))
            meta["global_iso"]["secs"] += time.perf_counter() - t0
            meta["global_iso"]["n_train"].append(len(train_idx))

            # --- epistasia global, ajuste conjunto ---
            t0 = time.perf_counter()
            r3, iso3, n_it = fit_global_joint(X_tr, y_tr)
            phi_held = r3.predict(X_held)
            preds["global_joint"][0][held] = iso3.predict(phi_held)
            if X_extra is not None:
                phi_extra = r3.predict(X_extra)
                preds["global_joint"][1][f] = iso3.predict(phi_extra)
                meta["global_joint"]["clip"].append(_frac_clipped(iso3, phi_extra))
            meta["global_joint"]["secs"] += time.perf_counter() - t0
            meta["global_joint"]["n_train"].append(len(train_idx))
            meta["global_joint"]["iters"].append(n_it)

        for mname in models:
            if not meta[mname]["n_train"]:
                continue
            cv_pred, extra = preds[mname]
            y_true, y_pred, loads = assemble_eval(
                d, cv_pred, extra.mean(axis=0), cv_pool_idx, extra_test_idx
            )
            if len(y_true) < 3:
                continue
            base = {
                "dataset": name,
                "modelo": mname,
                "featurizacao": "mut",
                "carga_treino": load,
                "n_treino": int(np.median(meta[mname]["n_train"])),
                "entrada": d.X_mut.shape[1],
                "segundos": round(meta[mname]["secs"], 1),
                "frac_truncada": (round(float(np.mean(meta[mname]["clip"])), 4)
                                  if meta[mname]["clip"] else 0.0),
                "iteracoes": (int(np.median(meta[mname]["iters"]))
                              if meta[mname]["iters"] else 0),
            }

            def record(mask, label):
                pr, sr = _corr(y_true[mask], y_pred[mask])
                rows.append({**base, "carga_teste": label,
                             "n_teste": int(mask.sum()),
                             "pearson": pr, "spearman": sr})

            record(np.ones(len(y_true), dtype=bool), "all")
            for k in sorted(set(loads.tolist())):
                km = loads == k
                if km.sum() >= 3:
                    record(km, str(int(k)))

        done = [r for r in rows if r["carga_treino"] == load and r["carga_teste"] == "all"]
        line = "  ".join(
            f"{r['modelo']}: r={r['pearson']:.4f} rho={r['spearman']:.4f}" for r in done
        )
        print(f"   carga {load}  {line}", flush=True)

    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--datasets", nargs="*", default=None)
    args = ap.parse_args()

    names = args.datasets or [n for n in ORDEM_CUSTO if n in DATASET_FILES]
    data_dir = Path(args.data_dir)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Gravacao INCREMENTAL: cada conjunto e anexado assim que termina, para que uma
    # interrupcao nao descarte o trabalho ja feito. Conjuntos ja presentes no
    # arquivo sao saltados, o que torna a execucao retomavel.
    feitos: set[str] = set()
    if out.exists() and out.stat().st_size > 0:
        try:
            feitos = set(pd.read_csv(out, sep="\t")["dataset"].unique())
            print(f"retomando: {len(feitos)} conjunto(s) ja no arquivo "
                  f"({', '.join(sorted(feitos))})", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"nao consegui ler o arquivo existente ({exc}); comecando limpo",
                  flush=True)

    total = 0
    for name in names:
        if name not in DATASET_FILES:
            sys.exit(f"conjunto desconhecido: {name!r}")
        if name in feitos:
            print(f"[{name}] ja consta no arquivo, saltando", flush=True)
            continue
        csv = data_dir / DATASET_FILES[name]
        if not csv.exists():
            print(f"  !! ausente: {csv.name}", flush=True)
            continue
        rows = run_dataset(csv, name)
        if not rows:
            continue
        header = (not out.exists()) or out.stat().st_size == 0
        pd.DataFrame(rows).to_csv(out, sep="\t", index=False, mode="a",
                                  header=header)
        total += len(rows)
        print(f"   -> {len(rows)} linhas anexadas a {out.name}", flush=True)

    print(f"\nconcluido. {total} linhas novas em {out}")


if __name__ == "__main__":
    main()
