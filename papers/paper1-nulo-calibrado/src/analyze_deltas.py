"""Duas leituras do delta pareado entre ridge aditivo e MULTI-evolve.

(A) INTERPOLACAO vs EXTRAPOLACAO. O proposito declarado do MULTI-evolve e
    extrapolar de singles/duplos para multimutantes de ordem alta. Separar as
    celulas em que a carga de teste esta DENTRO da faixa de treino (carga_teste <=
    carga_treino, interpolacao) das celulas em que esta FORA (extrapolacao) testa se
    a vantagem da FCNN esta onde o framework promete entregar.

(B) ASSIMETRIA PEARSON vs SPEARMAN. Spearman e invariante a transformacoes
    monotonicas das predicoes; Pearson nao. Uma paisagem aditiva composta com uma
    nao linearidade monotonica — epistasia GLOBAL ou nao especifica, que e efeito de
    escala e nao interacao entre mutacoes — penaliza o modelo aditivo em Pearson mas
    nao em Spearman. Portanto, se a vantagem da FCNN for sistematicamente maior em
    Pearson que em Spearman, ela e atribuivel a absorcao de nao linearidade de
    escala, nao a epistasia especifica.

Uso:
    python -I papers/paper1-nulo-calibrado/src/analyze_deltas.py \
        --comparison papers/paper1-nulo-calibrado/results/comparacao_s4.tsv
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon


def ci95(x: pd.Series) -> str:
    x = x.dropna()
    if len(x) < 2:
        return "n/d"
    lo = x.mean() - 1.96 * x.sem()
    hi = x.mean() + 1.96 * x.sem()
    return f"[{lo:+.4f}, {hi:+.4f}]"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparison", required=True)
    args = ap.parse_args()

    m = pd.read_csv(args.comparison, sep="\t")
    per_load = m[m["carga_teste"] != "all"].copy()
    per_load["carga_teste_n"] = per_load["carga_teste"].astype(int)

    print("=" * 78)
    print("(A) INTERPOLACAO vs EXTRAPOLACAO")
    print("=" * 78)
    per_load["regime"] = np.where(
        per_load["carga_teste_n"] <= per_load["carga_treino"],
        "interpolacao",
        "extrapolacao",
    )
    tab = per_load.groupby("regime").agg(
        celulas=("delta_spearman", "size"),
        delta_spearman_medio=("delta_spearman", "mean"),
        delta_spearman_mediana=("delta_spearman", "median"),
        delta_pearson_medio=("delta_pearson", "mean"),
    )
    print(tab.round(4).to_string())
    for reg, g in per_load.groupby("regime"):
        d = g["delta_spearman"].dropna()
        venc = int((d >= 0).sum())
        print(f"\n  {reg}: aditivo >= FCNN em {venc}/{len(d)} celulas "
              f"({100 * venc / len(d):.1f}%)")
        print(f"    delta medio {d.mean():+.4f}  IC95 {ci95(d)}")
        if len(d) >= 10:
            print(f"    Wilcoxon p = {wilcoxon(d).pvalue:.3g}")

    print("\n-- detalhe: extrapolacao por distancia da fronteira de treino --")
    per_load["distancia"] = per_load["carga_teste_n"] - per_load["carga_treino"]
    print(
        per_load[per_load["distancia"] > 0]
        .groupby("distancia")["delta_spearman"]
        .agg(["size", "mean"])
        .round(4)
        .to_string()
    )

    print("\n" + "=" * 78)
    print("(B) ASSIMETRIA PEARSON vs SPEARMAN")
    print("=" * 78)
    m2 = m.dropna(subset=["delta_spearman", "delta_pearson"]).copy()
    # Vantagem da FCNN = -delta. Se a vantagem for maior em Pearson que em
    # Spearman, entao (-delta_pearson) - (-delta_spearman) > 0, isto e
    # delta_spearman - delta_pearson > 0.
    m2["excesso_pearson"] = m2["delta_spearman"] - m2["delta_pearson"]

    print("\nVantagem da FCNN (= -delta), por carga de treino:")
    van = m2.groupby("carga_treino").agg(
        vant_spearman=("delta_spearman", lambda s: -s.mean()),
        vant_pearson=("delta_pearson", lambda s: -s.mean()),
    )
    van["excesso_em_pearson"] = van["vant_pearson"] - van["vant_spearman"]
    print(van.round(4).to_string())

    d = m2["excesso_pearson"].dropna()
    print(f"\nexcesso de vantagem em Pearson sobre Spearman: media {d.mean():+.4f}"
          f"  IC95 {ci95(d)}")
    print(f"  positivo em {int((d > 0).sum())}/{len(d)} celulas "
          f"({100 * (d > 0).mean():.1f}%)")
    print(f"  Wilcoxon p = {wilcoxon(d).pvalue:.3g}")

    print("\nPor conjunto (excesso de vantagem da FCNN em Pearson):")
    print(
        m2.groupby("dataset")["excesso_pearson"]
        .agg(["size", "mean"])
        .round(4)
        .sort_values("mean", ascending=False)
        .to_string()
    )


if __name__ == "__main__":
    main()
