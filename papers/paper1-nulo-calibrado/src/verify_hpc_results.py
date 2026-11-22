"""Verificacao independente dos resultados da reexecucao no HPC.

Recalcula do zero, a partir de merged.tsv, o pareamento FCNN vs ridge aditivo.
Motivo da verificacao: o arquivo analise_por_conjunto.txt que voltou do cluster
reporta 594 celulas de extrapolacao por featurizacao, enquanto o merge.py conta
297 — sinal de que as linhas do aditivo (identicas entre as duas tarefas de
featurizacao do mesmo conjunto) nao foram desduplicadas. Isso nao deveria mover as
medias por conjunto, mas infla n e invalida qualquer teste no nivel de celula.

Unidade de analise: o CONJUNTO. Celulas dentro de um mesmo conjunto compartilham
folds, dados e coeficientes, portanto nao sao independentes; agregamos por conjunto
antes de testar, e n = 12.

Uso:
    python -I papers/paper1-nulo-calibrado/src/verify_hpc_results.py \
        --merged fcnn_resultados/merged.tsv
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy.stats import binomtest, ttest_1samp, wilcoxon

KEY = ["dataset", "carga_treino", "carga_teste"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.merged, sep="\t")
    df["carga_teste"] = df["carga_teste"].astype(str)

    print("=" * 78)
    print("1. INTEGRIDADE DOS DADOS")
    print("=" * 78)
    print(f"linhas: {len(df)}")
    print("\ncobertura (conjuntos por modelo x featurizacao):")
    print(df.groupby(["modelo", "featurizacao"])["dataset"].nunique().to_string())

    fc = df[df["modelo"] == "fcnn"].copy()
    ad = df[df["modelo"] == "additive"].copy()

    # O aditivo e ajustado identicamente nas duas tarefas de featurizacao do
    # mesmo conjunto. Conferimos que de fato coincide antes de desduplicar.
    dup = ad.groupby(KEY)["spearman"].agg(["nunique", "size", "std"])
    n_multi = int((dup["size"] > 1).sum())
    max_std = float(dup["std"].max(skipna=True) or 0.0)
    print(f"\ncelulas do aditivo presentes mais de uma vez: {n_multi}")
    print(f"desvio maximo entre as copias: {max_std:.2e}  "
          f"({'identicas' if max_std < 1e-9 else 'DIVERGEM — investigar'})")

    ad_u = ad.drop_duplicates(subset=KEY)[KEY + ["pearson", "spearman"]].rename(
        columns={"pearson": "ad_pearson", "spearman": "ad_spearman"}
    )
    print(f"linhas do aditivo apos desduplicar: {len(ad_u)}  (antes: {len(ad)})")

    m = fc.merge(ad_u, on=KEY, how="inner")
    m["d_spearman"] = m["ad_spearman"] - m["spearman"]
    m["d_pearson"] = m["ad_pearson"] - m["pearson"]
    print(f"celulas pareadas: {len(m)}  "
          f"({len(m[m.featurizacao == 'mut'])} mut / "
          f"{len(m[m.featurizacao == 'seq'])} seq)")

    per_load = m[m["carga_teste"] != "all"].copy()
    per_load["ct"] = per_load["carga_teste"].astype(int)
    per_load["regime"] = np.where(
        per_load["ct"] <= per_load["carga_treino"], "interpolacao", "extrapolacao"
    )
    print("\ncelulas por featurizacao e regime (excluindo 'all'):")
    print(per_load.groupby(["featurizacao", "regime"]).size().to_string())

    print("\n" + "=" * 78)
    print("2. DELTA (aditivo - FCNN), UNIDADE = CONJUNTO, n = 12")
    print("=" * 78)
    print("delta > 0 favorece o ADITIVO.\n")

    rows = []
    for feat in ("mut", "seq"):
        for metric, col in (("spearman", "d_spearman"), ("pearson", "d_pearson")):
            for regime in ("extrapolacao", "interpolacao", "todos"):
                sub = per_load[per_load["featurizacao"] == feat]
                if regime != "todos":
                    sub = sub[sub["regime"] == regime]
                if sub.empty:
                    continue
                per_ds = sub.groupby("dataset")[col].mean()
                n = len(per_ds)
                mean = per_ds.mean()
                sem = per_ds.sem()
                pos = int((per_ds > 0).sum())
                w = wilcoxon(per_ds).pvalue if n >= 6 else np.nan
                t = ttest_1samp(per_ds, 0).pvalue if n >= 3 else np.nan
                b = binomtest(pos, n, 0.5).pvalue if n >= 3 else np.nan
                rows.append({
                    "feat": feat, "metrica": metric, "regime": regime,
                    "n_conj": n, "delta": round(mean, 4),
                    "ic95_lo": round(mean - 1.96 * sem, 4),
                    "ic95_hi": round(mean + 1.96 * sem, 4),
                    "aditivo_melhor": f"{pos}/{n}",
                    "p_wilcoxon": round(w, 4), "p_t": round(t, 4),
                    "p_sinais": round(b, 4),
                    "n_celulas": len(sub),
                })
    res = pd.DataFrame(rows)
    print(res.to_string(index=False))

    print("\n" + "=" * 78)
    print("3. A ASSIMETRIA PEARSON vs SPEARMAN")
    print("=" * 78)
    print("Spearman e invariante a transformacao monotonica das predicoes; Pearson")
    print("nao. Vantagem da FCNN maior em Pearson que em Spearman => ela esta")
    print("absorvendo nao linearidade de escala (epistasia GLOBAL), nao interacao.\n")
    for feat in ("mut", "seq"):
        for regime in ("extrapolacao", "interpolacao"):
            sub = per_load[(per_load.featurizacao == feat)
                           & (per_load.regime == regime)]
            ds_s = sub.groupby("dataset")["d_spearman"].mean()
            ds_p = sub.groupby("dataset")["d_pearson"].mean()
            excesso = ds_s - ds_p   # vantagem_pearson - vantagem_spearman
            w = wilcoxon(excesso).pvalue if len(excesso) >= 6 else np.nan
            print(f"  {feat:>3} / {regime:<13} excesso em Pearson = "
                  f"{excesso.mean():+.4f}  IC95 "
                  f"[{excesso.mean() - 1.96 * excesso.sem():+.4f}, "
                  f"{excesso.mean() + 1.96 * excesso.sem():+.4f}]  "
                  f"positivo em {int((excesso > 0).sum())}/{len(excesso)}  "
                  f"Wilcoxon p = {w:.4f}")

    print("\n" + "=" * 78)
    print("4. POR CARGA DE TREINO (Spearman global, celulas 'all')")
    print("=" * 78)
    glob = m[m["carga_teste"] == "all"]
    piv = glob.pivot_table(index="featurizacao", columns="carga_treino",
                           values=["spearman", "ad_spearman"])
    print(piv.round(4).to_string())
    print("\ndelta por carga de treino (unidade = conjunto):")
    for feat in ("mut", "seq"):
        sub = glob[glob.featurizacao == feat]
        for load in (1, 2, 3):
            s = sub[sub.carga_treino == load]["d_spearman"]
            if len(s) >= 3:
                print(f"  {feat} carga {load}: delta {s.mean():+.4f}  "
                      f"IC95 [{s.mean() - 1.96 * s.sem():+.4f}, "
                      f"{s.mean() + 1.96 * s.sem():+.4f}]  "
                      f"aditivo melhor em {int((s > 0).sum())}/{len(s)}")

    print("\n" + "=" * 78)
    print("5. CUSTO")
    print("=" * 78)
    cost = fc.groupby(["dataset", "featurizacao"])["segundos"].max().unstack()
    cost["total"] = cost.sum(axis=1)
    print(cost.round(1).sort_values("total", ascending=False).to_string())
    print(f"\ntempo total de treino somado: {cost['total'].sum() / 60:.1f} min")
    print(f"pior tarefa isolada: {fc['segundos'].max() / 60:.1f} min")
    print(f"epocas efetivas: mediana {fc['epocas_medianas'].median():.0f}  "
          f"faixa {fc['epocas_medianas'].min():.0f}-{fc['epocas_medianas'].max():.0f}"
          f"  (teto era 300)")


if __name__ == "__main__":
    main()
