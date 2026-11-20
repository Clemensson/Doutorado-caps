"""Protocolo de benchmarking alinhado ao de Tran et al. (Fig. 2E/F), com nulo aditivo.

Este modulo replica as particoes do artigo original, para que a comparacao entre o
modelo aditivo e os numeros publicados seja pareada em vez de indicativa. O protocolo
foi reconstruido a partir de tres fontes convergentes:

1. `multievolve/utils/benchmark_utils.py::preprocess_dataset` — o filtro de
   estringencia 'singles': mantem apenas variantes cujas mutacoes constituintes
   TODAS existam como singles medidas no conjunto. E o que produz as contagens
   "Post-filtering" da Tabela S7.
2. `multievolve/splitters/base_splitters.py::MutLoadProteinSplitter` — corte por
   carga mutacional.
3. `multievolve-baselines/analysis/additive-proteingym_fig2ef.ipynb` do DeWitt lab —
   a reconstrucao explicita do protocolo da Fig. 2E/F, que resolve a ambiguidade
   de como cargas de teste <= 3 coexistem com treino de carga 3.

Protocolo:
  1. Filtro de estringencia 'singles'.
  2. Normalizacao min-max de DMS_score para [0, 1]  <- escala usada no artigo.
  3. Matriz de desenho binaria sobre as mutacoes pontuais distintas.
  4. Particao: pool de CV = cargas 1-3;  teste extra = cargas >= 4.
  5. Pool de CV dividido em 5 folds (seed 42).
  6. Para cada carga maxima de treino L em {1,2,3} e cada fold: ajustar nos
     variantes de carga <= L dos outros 4 folds; predizer o fold retido e o
     teste extra.
  7. Variantes do pool de CV recebem a predicao do fold em que foram retidos;
     variantes do teste extra recebem a media das 5 predicoes.
  8. Avaliar em cargas >= 3, global e estratificado por carga exata.

ATENCAO: a ordenacao de empates em `sort_values(by='num_mutations')` nao e garantida
entre implementacoes, portanto a composicao exata dos folds pode diferir da do
notebook de referencia. O efeito e de variabilidade amostral, nao sistematico; a
funcao aceita `seed` para quantifica-lo por reamostragem.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import RidgeCV

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape import DATASET_NAMES  # noqa: E402

RIDGE_ALPHAS = np.logspace(-3, 3, 50)
TRAIN_LOADS = (1, 2, 3)
N_FOLDS = 5
SINGLE_RE = re.compile(r"^[A-Z]\d+[A-Z]$")


def preprocess_singles_stringency(csv_path: Path) -> pd.DataFrame:
    """Replica preprocess_dataset(..., stringency='singles') de Tran et al.

    Mantem apenas variantes cujas mutacoes constituintes todas aparecam como
    single mutante medido. Reimplementado em vez de importado para nao arrastar
    as dependencias pesadas do pacote original (torch, transformers).
    """
    df = pd.read_csv(csv_path, usecols=["mutant", "DMS_score"])
    df = df.dropna(subset=["mutant", "DMS_score"]).copy()
    df["mutant"] = df["mutant"].astype(str)
    df["tokens"] = df["mutant"].str.split(":")
    df["num_mutations"] = df["tokens"].str.len()

    singles = set(
        df.loc[df["num_mutations"] == 1, "mutant"].tolist()
    )
    keep = df["tokens"].apply(lambda toks: all(t in singles for t in toks))
    df = df[keep]

    # preprocess_dataset ordena por num_mutations decrescente; replicamos de
    # forma estavel para que a ordem seja deterministica aqui.
    df = df.sort_values(by="num_mutations", ascending=False, kind="stable")
    return df.reset_index(drop=True)


def build_design(df: pd.DataFrame) -> tuple[sp.csr_matrix, list[str]]:
    vocab = sorted({t for toks in df["tokens"] for t in toks})
    index = {m: j for j, m in enumerate(vocab)}
    rows, cols = [], []
    for i, toks in enumerate(df["tokens"]):
        for t in toks:
            rows.append(i)
            cols.append(index[t])
    X = sp.csr_matrix(
        (np.ones(len(rows)), (rows, cols)), shape=(len(df), len(vocab))
    )
    return X, vocab


def _corr(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    if np.std(p) <= 0 or np.std(y) <= 0:
        return 0.0, 0.0
    return float(pearsonr(y, p).statistic), float(spearmanr(y, p).statistic)


def benchmark_additive(
    csv_path: Path, dataset_name: str, seed: int = 42, n_folds: int = N_FOLDS
) -> list[dict]:
    """Roda o protocolo alinhado usando APENAS ridge aditivo."""
    df = preprocess_singles_stringency(csv_path)
    n_muts = df["num_mutations"].to_numpy()

    y = df["DMS_score"].to_numpy(dtype=float)
    ymin, ymax = float(y.min()), float(y.max())
    if ymax > ymin:
        y = (y - ymin) / (ymax - ymin)

    X, vocab = build_design(df)
    n_total = len(df)

    cv_pool_idx = np.where((n_muts >= 1) & (n_muts <= 3))[0]
    extra_test_idx = np.where(n_muts >= 4)[0]
    if len(cv_pool_idx) < n_folds:
        return []

    rng = np.random.RandomState(seed)
    shuffled = cv_pool_idx.copy()
    rng.shuffle(shuffled)
    folds = np.array_split(shuffled, n_folds)

    results: list[dict] = []
    for load in TRAIN_LOADS:
        y_pred_cv = np.full(n_total, np.nan)
        y_pred_extra = np.zeros((n_folds, len(extra_test_idx)))
        n_train_per_fold: list[int] = []
        alphas: list[float] = []

        for f in range(n_folds):
            held = folds[f]
            pool = np.concatenate([folds[j] for j in range(n_folds) if j != f])
            train_idx = pool[n_muts[pool] <= load]
            if len(train_idx) < 3:
                continue

            # Treino denso (subconjunto pequeno: cargas <= 3), predicao esparsa.
            X_tr = np.asarray(X[train_idx].todense())
            model = RidgeCV(alphas=RIDGE_ALPHAS, fit_intercept=True)
            model.fit(X_tr, y[train_idx])
            n_train_per_fold.append(len(train_idx))
            alphas.append(float(model.alpha_))

            y_pred_cv[held] = model.predict(X[held])
            if len(extra_test_idx) > 0:
                y_pred_extra[f] = model.predict(X[extra_test_idx])

        if not n_train_per_fold:
            continue

        extra_mean = y_pred_extra.mean(axis=0)

        # Conjunto de avaliacao: pool de CV com carga >= 3 + todo o teste extra
        sel = cv_pool_idx[(n_muts[cv_pool_idx] >= 3) & ~np.isnan(y_pred_cv[cv_pool_idx])]
        eval_true = np.concatenate([y[sel], y[extra_test_idx]])
        eval_pred = np.concatenate([y_pred_cv[sel], extra_mean])
        eval_loads = np.concatenate([n_muts[sel], n_muts[extra_test_idx]])
        if len(eval_true) < 3:
            continue

        pr, sr = _corr(eval_true, eval_pred)
        results.append(
            {
                "dataset": dataset_name,
                "carga_treino": load,
                "carga_teste": "all",
                "n_treino": int(np.median(n_train_per_fold)),
                "n_teste": len(eval_true),
                "p_features": X.shape[1],
                "alpha": float(np.median(alphas)),
                "pearson": pr,
                "spearman": sr,
            }
        )

        for k in sorted(set(eval_loads.tolist())):
            km = eval_loads == k
            if km.sum() < 3:
                continue
            pr_k, sr_k = _corr(eval_true[km], eval_pred[km])
            results.append(
                {
                    "dataset": dataset_name,
                    "carga_treino": load,
                    "carga_teste": str(int(k)),
                    "n_treino": int(np.median(n_train_per_fold)),
                    "n_teste": int(km.sum()),
                    "p_features": X.shape[1],
                    "alpha": float(np.median(alphas)),
                    "pearson": pr_k,
                    "spearman": sr_k,
                }
            )

    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--datasets", nargs="*", default=None)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    stem_by_name = {v: k for k, v in DATASET_NAMES.items()}

    if args.datasets:
        stems = [stem_by_name.get(n, n) for n in args.datasets]
    else:
        stems = sorted(DATASET_NAMES)

    rows: list[dict] = []
    for stem in stems:
        csv = data_dir / f"{stem}.csv"
        if not csv.exists():
            print(f"  !! ausente: {csv.name}", flush=True)
            continue
        name = DATASET_NAMES.get(stem, stem)
        res = benchmark_additive(csv, name, seed=args.seed)
        rows.extend(res)
        overall = [r for r in res if r["carga_teste"] == "all"]
        line = "  ".join(
            f"L{r['carga_treino']}={r['spearman']:.4f}" for r in overall
        )
        print(f"[{name}] n_feat={res[0]['p_features'] if res else '?'}  {line}", flush=True)

    df = pd.DataFrame(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, sep="\t", index=False)
    print(f"\nescrito: {out}  ({len(df)} linhas)")


if __name__ == "__main__":
    main()
