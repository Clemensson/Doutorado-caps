"""Junta as saidas das tarefas do array e resume a comparacao pareada.

Uso:  python src/merge.py --results-dir results --out merged.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results")
    ap.add_argument("--out", default="merged.tsv")
    args = ap.parse_args()

    files = sorted(Path(args.results_dir).glob("*.tsv"))
    if not files:
        raise SystemExit(f"nenhum .tsv em {args.results_dir}")
    df = pd.concat([pd.read_csv(f, sep="\t") for f in files], ignore_index=True)
    df.to_csv(args.out, sep="\t", index=False)
    print(f"{len(files)} arquivos, {len(df)} linhas -> {args.out}\n")

    esperado = 24
    if len(files) < esperado:
        faltam = esperado - len(files)
        print(f"!! ATENCAO: {faltam} tarefa(s) do array ausente(s) — "
              f"esperados {esperado} arquivos\n")

    print("== cobertura ==")
    print(df.groupby(["modelo", "featurizacao"])["dataset"].nunique().to_string())

    glob = df[df["carga_teste"] == "all"]
    print("\n== Spearman global por modelo e carga de treino ==")
    print(
        glob.pivot_table(
            index=["modelo", "featurizacao"], columns="carga_treino", values="spearman"
        ).round(4).to_string()
    )

    # Pareamento FCNN vs aditivo dentro de cada celula
    fc = df[df["modelo"] == "fcnn"]
    ad = df[df["modelo"] == "additive"][
        ["dataset", "carga_treino", "carga_teste", "pearson", "spearman"]
    ].rename(columns={"pearson": "ad_pearson", "spearman": "ad_spearman"})
    # O aditivo e identico entre as duas tarefas de featurizacao do mesmo conjunto;
    # deduplicamos para nao contar duas vezes.
    ad = ad.drop_duplicates(subset=["dataset", "carga_treino", "carga_teste"])

    m = fc.merge(ad, on=["dataset", "carga_treino", "carga_teste"], how="inner")
    m["delta_spearman"] = m["ad_spearman"] - m["spearman"]
    m["delta_pearson"] = m["ad_pearson"] - m["pearson"]

    print("\n== delta (aditivo - FCNN), pareado nos mesmos folds ==")
    for feat, g in m.groupby("featurizacao"):
        d = g["delta_spearman"].dropna()
        print(f"\n  featurizacao {feat!r}: {len(d)} celulas")
        print(f"    delta Spearman medio {d.mean():+.4f}  mediana {d.median():+.4f}")
        print(f"    aditivo >= FCNN em {int((d >= 0).sum())}/{len(d)}")
        if len(d) >= 10:
            print(f"    Wilcoxon p = {wilcoxon(d).pvalue:.3g}")
        dp = g["delta_pearson"].dropna()
        print(f"    delta Pearson medio {dp.mean():+.4f}")
        print(f"    excesso de vantagem da FCNN em Pearson: "
              f"{(d.mean() - dp.mean()):+.4f}")

    per_load = m[m["carga_teste"] != "all"].copy()
    per_load["ct"] = per_load["carga_teste"].astype(int)
    per_load["regime"] = np.where(
        per_load["ct"] <= per_load["carga_treino"], "interpolacao", "extrapolacao"
    )
    print("\n== interpolacao vs extrapolacao (delta Spearman) ==")
    print(
        per_load.groupby(["featurizacao", "regime"])["delta_spearman"]
        .agg(["size", "mean", "median"]).round(4).to_string()
    )

    print("\n== custo efetivo ==")
    print(
        fc.groupby("dataset")
        .agg(segundos=("segundos", "max"), epocas=("epocas_medianas", "median"))
        .round(1).sort_values("segundos", ascending=False).to_string()
    )


if __name__ == "__main__":
    main()
