"""Comparacao PAREADA do ridge aditivo contra a Tabela S4 de Tran et al.

Diferente de `compare_to_tran.py` (que era indicativo, por usar particoes nossas),
aqui o aditivo roda no protocolo alinhado de `aligned_protocol.py` — mesmo filtro de
estringencia, mesma normalizacao min-max, mesma particao pool-de-CV/teste-extra,
mesmos 5 folds — de modo que cada celula (conjunto x carga de treino x carga de
teste) e comparavel.

Uso:
    python -I papers/paper1-nulo-calibrado/src/compare_to_s4.py \
        --aligned papers/paper1-nulo-calibrado/results/alinhado_all.tsv \
        --s4 "data/external/zenodo-18240028/Table S4 ....xlsx" \
        --out papers/paper1-nulo-calibrado/results/comparacao_s4.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aligned", required=True)
    ap.add_argument("--s4", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    add = pd.read_csv(args.aligned, sep="\t")
    add["carga_teste"] = add["carga_teste"].astype(str)
    add = add.rename(
        columns={"spearman": "aditivo_spearman", "pearson": "aditivo_pearson"}
    )

    s4 = pd.read_excel(args.s4)
    s4 = s4.rename(
        columns={
            "Dataset Name": "dataset",
            "Max mutational load of train set": "carga_treino",
            "Mutational load of test set": "carga_teste",
            "Spearman's r": "multievolve_spearman",
            "Pearson's r": "multievolve_pearson",
        }
    )
    s4["carga_teste"] = s4["carga_teste"].astype(str)
    s4 = s4[
        ["dataset", "carga_treino", "carga_teste",
         "multievolve_spearman", "multievolve_pearson"]
    ]

    m = add.merge(s4, on=["dataset", "carga_treino", "carga_teste"], how="inner")
    m["delta_spearman"] = m["aditivo_spearman"] - m["multievolve_spearman"]
    m["delta_pearson"] = m["aditivo_pearson"] - m["multievolve_pearson"]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    m.to_csv(out, sep="\t", index=False)

    print("=" * 78)
    print("COMPARACAO PAREADA — ridge aditivo vs MULTI-evolve (Tabela S4)")
    print("=" * 78)
    print(f"celulas comparaveis: {len(m)}\n")

    glob = m[m["carga_teste"] == "all"]
    print("== Avaliacao global ('all'), Spearman ==")
    piv = glob.pivot_table(
        index="dataset",
        columns="carga_treino",
        values=["aditivo_spearman", "multievolve_spearman"],
    )
    print(piv.round(4).to_string())

    print("\n== delta medio (aditivo - MULTI-evolve), por carga de treino ==")
    print(
        m.groupby("carga_treino")[["delta_spearman", "delta_pearson"]]
        .agg(["mean", "median", "std", "count"])
        .round(4)
        .to_string()
    )

    print("\n== delta medio por carga de TESTE (Spearman) ==")
    by_test = m.copy()
    by_test["ordem"] = by_test["carga_teste"].map(
        lambda s: 999 if s == "all" else int(s)
    )
    print(
        by_test.sort_values("ordem")
        .groupby("carga_teste", sort=False)["delta_spearman"]
        .agg(["mean", "count"])
        .round(4)
        .to_string()
    )

    n_win = int((m["delta_spearman"] >= 0).sum())
    print(f"\n== o ADITIVO iguala ou supera em {n_win} de {len(m)} celulas "
          f"({100 * n_win / len(m):.1f}%) ==")

    print("\n== celulas com maior vantagem do MULTI-evolve (candidatos a epistasia real) ==")
    worst = m.nsmallest(12, "delta_spearman")[
        ["dataset", "carga_treino", "carga_teste", "n_teste",
         "aditivo_spearman", "multievolve_spearman", "delta_spearman"]
    ]
    print(worst.round(4).to_string(index=False))

    print("\n== teste de sinal sobre o delta (todas as celulas) ==")
    d = m["delta_spearman"].dropna()
    pos, neg = int((d > 0).sum()), int((d < 0).sum())
    print(f"  aditivo melhor: {pos}   MULTI-evolve melhor: {neg}")
    print(f"  delta medio: {d.mean():.4f}  (IC95% aprox: "
          f"{d.mean() - 1.96 * d.sem():.4f} a {d.mean() + 1.96 * d.sem():.4f})")
    print(f"  correlacao entre as duas series: "
          f"{np.corrcoef(m['aditivo_spearman'], m['multievolve_spearman'])[0, 1]:.4f}")

    print(f"\nescrito: {out}")


if __name__ == "__main__":
    main()
