"""A epistasia global e efeito de ESCALA ou de CENSURA do ensaio?

MOTIVACAO. O capitulo mostrou que um modelo monotonico sem interacao
(y ~ g(x'beta)) recupera metade da vantagem da FCNN em Pearson. Restava decidir de
que natureza e essa nao linearidade. A especificacao previa "replicacao em escala
log", sob o argumento biofisico de que efeitos mutacionais se somam em escala
logaritmica quando sao contribuicoes termodinamicas independentes.

Mas inspecionar os dados mostrou que a pergunta estava mal posta. O log e impossivel
na maioria dos conjuntos, e por razoes que importam:

  AAV2 VP1, scFv          ja estao em log (faixas simetricas em torno de zero)
  ppluGFP2/amac/cgreGFP   intensidade bruta de 449 a 40.087 — os unicos candidatos
  IGP dehydratase         148.064 de 254.782 variantes valem EXATAMENTE zero
  TrpB, GB1               35.250 e 29.477 zeros exatos

Zeros exatos em massa nao sao um problema de escala: sao variantes no PISO do ensaio,
ou seja CENSURA. Nenhuma transformacao monotonica conserta censura, e a isotonica
pode estar simplesmente aprendendo o piso — mapeando uma faixa larga de valores
latentes no unico valor zero. Formalmente isso e epistasia global; biologicamente e
limite de deteccao, nao nao linearidade termodinamica.

Dai as duas perguntas deste modulo:

  (1) ESCALA. Nos tres conjuntos de intensidade bruta, o ajuste aditivo em log
      recupera o ganho da isotonica? Se sim, a nao linearidade E logaritmica, e a
      "epistasia global" e artefato de ter ajustado na escala errada.

  (2) CENSURA. Nos conjuntos com zeros em massa, o ganho da isotonica sobrevive
      quando se restringe aos variantes acima do piso? Se colapsa, o que a isotonica
      aprendia era o piso do ensaio.

Em ambos os casos a quantidade comparada e o GANHO da isotonica sobre o aditivo
dentro da mesma configuracao — os valores absolutos nao sao comparaveis entre
configuracoes porque o conjunto de teste ou a escala mudam.

Uso:
    python -I papers/paper1-nulo-calibrado/src/scale_and_censoring.py \
        --data-dir data/external/zenodo-17620759 \
        --out papers/paper1-nulo-calibrado/results/escala_censura.tsv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import RidgeCV

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "hpc_fcnn_rerun" / "src"))
from data import assemble_eval, load_dataset, make_partition  # noqa: E402

ALPHAS = np.logspace(-3, 3, 50)
CARGA = 3

# (1) intensidade bruta, estritamente positiva: o log e bem posto
INTENSIDADE = ["ppluGFP2", "amacGFP", "cgreGFP"]
# (2) zeros exatos em massa: suspeita de censura no piso do ensaio
CENSURADOS = ["IGP dehydratase", "TrpB", "GB1", "ParD3"]


def scores_brutos_alinhados(csv: Path) -> np.ndarray:
    """DMS_score original na MESMA ordem de linhas que load_dataset produz.

    Replica o filtro de estringencia 'singles' e a ordenacao decrescente por carga
    mutacional de data.py. Precisa ser a mesma ordem porque os folds derivam dela —
    realinhar por posicao depois do filtro nao funciona, e foi o bug da primeira
    versao deste modulo.
    """
    df = pd.read_csv(csv, usecols=["mutant", "DMS_score"])
    df = df.dropna(subset=["mutant", "DMS_score"]).copy()
    df["mutant"] = df["mutant"].astype(str)
    toks = df["mutant"].str.split(":")
    n_muts = toks.str.len().to_numpy()
    singles = set(df.loc[n_muts == 1, "mutant"].tolist())
    keep = toks.apply(lambda t: all(x in singles for x in t)).to_numpy()
    df, n_muts = df[keep], n_muts[keep]
    order = np.argsort(-n_muts, kind="stable")
    return df["DMS_score"].to_numpy(dtype=float)[order]


def _corr(y, p):
    if np.std(p) <= 0 or np.std(y) <= 0:
        return 0.0, 0.0
    return float(pearsonr(y, p).statistic), float(spearmanr(y, p).statistic)


def pipeline(X, y, folds, cv_pool_idx, extra_test_idx, n_muts, keep=None):
    """Aditivo e isotonica nos mesmos folds. `keep` restringe a avaliacao."""
    n = len(y)
    pred = {m: (np.full(n, np.nan), np.zeros((len(folds), len(extra_test_idx))))
            for m in ("additive", "global_iso")}
    for f, held in enumerate(folds):
        pool = np.concatenate([folds[j] for j in range(len(folds)) if j != f])
        tr = pool[n_muts[pool] <= CARGA]
        if keep is not None:
            tr = tr[keep[tr]]
        if len(tr) < 10:
            continue
        Xtr = np.asarray(X[tr].todense())
        m = RidgeCV(alphas=ALPHAS, fit_intercept=True).fit(Xtr, y[tr])
        pred["additive"][0][held] = m.predict(X[held])
        pred["additive"][1][f] = m.predict(X[extra_test_idx])
        iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
        iso.fit(m.predict(Xtr), y[tr])
        pred["global_iso"][0][held] = iso.predict(m.predict(X[held]))
        pred["global_iso"][1][f] = iso.predict(m.predict(X[extra_test_idx]))

    out = {}
    for mname, (cv, extra) in pred.items():
        yt, yp, _ = assemble_eval(
            type("D", (), {"y": y, "n_muts": n_muts})(), cv, extra.mean(axis=0),
            cv_pool_idx, extra_test_idx)
        sel = cv_pool_idx[(n_muts[cv_pool_idx] >= 3) & ~np.isnan(cv[cv_pool_idx])]
        idx = np.concatenate([sel, extra_test_idx])
        if keep is not None:
            mask = keep[idx]
            yt, yp = yt[mask], yp[mask]
        if len(yt) < 10:
            continue
        out[mname] = (*_corr(yt, yp), len(yt))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = pd.read_csv(ROOT / "hpc_fcnn_rerun" / "config" / "datasets.tsv", sep="\t")
    arq = dict(zip(cfg["dataset"], cfg["arquivo"], strict=True))
    rows = []

    print("=" * 78)
    print("(1) ESCALA — o log recupera o ganho da isotonica?")
    print("=" * 78)
    for name in INTENSIDADE:
        csv = Path(args.data_dir) / arq[name]
        for escala in ("identity", "log"):
            d = load_dataset(csv, name, need_seq=False)
            if escala == "log":
                raw = scores_brutos_alinhados(csv)
                assert len(raw) == len(d.y), (
                    f"{name}: {len(raw)} brutos vs {len(d.y)} filtrados")
                assert raw.min() > 0, f"{name}: ha valores <= 0, log mal posto"
                y = np.log(raw)
                # re-normaliza para [0,1] para que as magnitudes sejam comparaveis
                y = (y - y.min()) / (y.max() - y.min())
            else:
                y = d.y
            folds, cvp, ext = make_partition(d)
            res = pipeline(d.X_mut.tocsr(), y, folds, cvp, ext, d.n_muts)
            if not {"additive", "global_iso"} <= set(res):
                continue
            ga = res["global_iso"][0] - res["additive"][0]
            gs = res["global_iso"][1] - res["additive"][1]
            rows.append({"pergunta": "escala", "dataset": name, "config": escala,
                         "r_aditivo": res["additive"][0],
                         "r_isotonica": res["global_iso"][0],
                         "ganho_pearson": ga, "ganho_spearman": gs,
                         "n_aval": res["additive"][2]})
            print(f"  {name:<10} {escala:<9} aditivo r={res['additive'][0]:.4f}  "
                  f"isotonica r={res['global_iso'][0]:.4f}  ganho={ga:+.4f}")

    print("\n" + "=" * 78)
    print("(2) CENSURA — o ganho sobrevive acima do piso do ensaio?")
    print("=" * 78)
    for name in CENSURADOS:
        csv = Path(args.data_dir) / arq[name]
        d = load_dataset(csv, name, need_seq=False)
        folds, cvp, ext = make_partition(d)
        piso = float(np.min(d.y))
        no_piso = np.isclose(d.y, piso)
        print(f"  {name}: {no_piso.sum()} de {d.n} variantes no piso "
              f"({100 * no_piso.mean():.1f}%)")
        for config, keep in (("completo", None), ("acima_do_piso", ~no_piso)):
            res = pipeline(d.X_mut.tocsr(), d.y, folds, cvp, ext, d.n_muts, keep)
            if not {"additive", "global_iso"} <= set(res):
                continue
            ga = res["global_iso"][0] - res["additive"][0]
            gs = res["global_iso"][1] - res["additive"][1]
            rows.append({"pergunta": "censura", "dataset": name, "config": config,
                         "r_aditivo": res["additive"][0],
                         "r_isotonica": res["global_iso"][0],
                         "ganho_pearson": ga, "ganho_spearman": gs,
                         "n_aval": res["additive"][2]})
            print(f"      {config:<14} aditivo r={res['additive'][0]:.4f}  "
                  f"isotonica r={res['global_iso'][0]:.4f}  ganho={ga:+.4f}  "
                  f"n={res['additive'][2]}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, sep="\t", index=False)
    print(f"\nescrito: {out}")


if __name__ == "__main__":
    main()
