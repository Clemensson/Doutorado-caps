"""Autoteste da camada de dados — NAO requer PyTorch.

Verifica, para um conjunto: o filtro de estringencia, a normalizacao de y, as duas
featurizacoes, a particao em folds e a equivalencia afim entre as representacoes.

Uso:  python -I scripts/selftest_data.py --data-dir ../data/external/zenodo-17620759 \
          --dataset NucB
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from data import N_CATEGORIES, assemble_eval, load_dataset, make_partition  # noqa: E402

FAIL = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global FAIL
    print(f"  [{'ok ' if ok else 'FALHA'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAIL += 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--dataset", default="NucB")
    args = ap.parse_args()

    cfg = pd.read_csv(ROOT / "config" / "datasets.tsv", sep="\t")
    row = cfg[cfg["dataset"] == args.dataset].iloc[0]
    csv = Path(args.data_dir) / row["arquivo"]
    print(f"conjunto {args.dataset}  arquivo {csv.name}")

    d = load_dataset(csv, args.dataset, need_seq=True)
    print(f"  n={d.n}  p_mut={d.X_mut.shape[1]}  L={d.seq_len}  "
          f"entrada_seq={d.input_dim('seq')}")

    check("comprimento de sequencia bate com config", d.seq_len == int(row["seq_len"]),
          f"{d.seq_len} vs {row['seq_len']}")
    check("y normalizado em [0,1]",
          abs(d.y.min()) < 1e-9 and abs(d.y.max() - 1.0) < 1e-9,
          f"min={d.y.min():.3g} max={d.y.max():.3g}")
    check("sem NaN em y", not np.isnan(d.y).any())
    check("cargas mutacionais positivas", d.n_muts.min() >= 1)

    # Filtro de estringencia: toda mutacao presente deve existir como single.
    singles_cols = np.asarray(d.X_mut[d.n_muts == 1].sum(axis=0)).ravel() > 0
    check("estringencia 'singles': toda coluna usada tem single medido",
          bool(singles_cols.all()),
          f"{int((~singles_cols).sum())} colunas sem single")

    # Indicador de mutacao: soma da linha == carga
    rowsum = np.asarray(d.X_mut.sum(axis=1)).ravel()
    check("soma do indicador == carga mutacional",
          bool(np.array_equal(rowsum.astype(int), d.n_muts)))

    # One-hot de sequencia: exatamente uma categoria ativa por posicao
    idx = np.arange(min(200, d.n))
    Xs = d.featurize(idx, "seq")
    per_pos = Xs.reshape(len(idx), d.seq_len, N_CATEGORIES).sum(axis=2)
    check("one-hot de sequencia: 1 categoria ativa por posicao",
          bool(np.allclose(per_pos, 1.0)))
    check("dimensao do one-hot de sequencia",
          Xs.shape == (len(idx), d.seq_len * N_CATEGORIES), str(Xs.shape))

    # Equivalencia afim: o one-hot de sequencia deve ser recuperavel por regressao
    # linear sobre o indicador de mutacao (mais intercepto). Verificamos pelo
    # inverso, que e mais barato: duas variantes com o mesmo indicador tem o mesmo
    # one-hot de sequencia.
    Xm = d.featurize(idx, "mut")
    keys_m = [tuple(np.flatnonzero(r)) for r in Xm]
    keys_s = [Xs[i].tobytes() for i in range(len(idx))]
    dup = {}
    consistent = True
    for km, ks in zip(keys_m, keys_s, strict=True):
        if km in dup and dup[km] != ks:
            consistent = False
            break
        dup[km] = ks
    check("indicador identico => one-hot de sequencia identico (equivalencia afim)",
          consistent)

    folds, cv_pool, extra = make_partition(d)
    sizes = [len(f) for f in folds]
    check("5 folds", len(folds) == 5, str(sizes))
    allf = np.concatenate(folds)
    check("folds particionam o pool de CV sem repeticao",
          len(np.unique(allf)) == len(allf) == len(cv_pool))
    check("pool de CV sao cargas 1-3",
          bool(((d.n_muts[cv_pool] >= 1) & (d.n_muts[cv_pool] <= 3)).all()))
    check("teste extra sao cargas >= 4",
          bool((d.n_muts[extra] >= 4).all()) if len(extra) else True,
          f"n={len(extra)}")
    check("pool de CV e teste extra sao disjuntos",
          len(np.intersect1d(cv_pool, extra)) == 0)

    # Determinismo da particao
    folds2, _, _ = make_partition(d)
    check("particao e deterministica",
          all(np.array_equal(a, b) for a, b in zip(folds, folds2, strict=True)))

    # assemble_eval
    pred = np.full(d.n, np.nan)
    pred[cv_pool] = 0.5
    yt, yp, loads = assemble_eval(d, pred, np.zeros(len(extra)), cv_pool, extra)
    check("avaliacao cobre apenas cargas >= 3",
          bool((loads >= 3).all()), f"n_eval={len(yt)}")

    print(f"\n{'TODOS OS TESTES PASSARAM' if FAIL == 0 else f'{FAIL} FALHA(S)'}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
