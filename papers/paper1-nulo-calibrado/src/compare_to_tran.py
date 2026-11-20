"""Compara o ridge aditivo (marco zero) com os numeros publicados de MULTI-evolve.

Os valores de referencia vem da Tabela S3 do suplementar de Tran et al., filtrando
as linhas de feature 'One-hot', que e a unica rodada nas tres cargas de treino (1, 2
e 3) e tambem a melhor feature na carga 2.

ATENCAO A INTERPRETACAO: as particoes nao sao identicas. O nosso desenho fixa o teste
em variantes de ordem >= 4 para que a unica coisa que varie entre cargas seja o
enriquecimento do treino. O desenho de Tran et al. precisa ser lido da Tabela S4
(colunas 'Max mutational load of train set' e 'Mutational load of test set') antes de
qualquer comparacao pareada. Portanto esta tabela e **indicativa**, nao um confronto
controlado: ela mostra ordens de grandeza e a forma da progressao, nao uma diferenca
atribuivel.

Uso:
    python -I papers/paper1-nulo-calibrado/src/compare_to_tran.py \
        --additive papers/paper1-nulo-calibrado/results/milestone0_all.tsv \
        --s3 "data/external/zenodo-18240028/Table S3 ...xlsx" \
        --out papers/paper1-nulo-calibrado/results/comparacao_tran.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--additive", required=True)
    ap.add_argument("--s3", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    add = pd.read_csv(args.additive, sep="\t")
    add = add[add["nota"].isna() | (add["nota"] == "")]
    add = add[["dataset", "carga_treino", "spearman", "n_treino"]].rename(
        columns={"spearman": "aditivo_spearman"}
    )

    s3 = pd.read_excel(args.s3)
    me = s3[s3["Feature"] == "One-hot"][
        ["Dataset Name", "Training Load", "Spearman - Test"]
    ].rename(
        columns={
            "Dataset Name": "dataset",
            "Training Load": "carga_treino",
            "Spearman - Test": "multievolve_spearman",
        }
    )

    merged = add.merge(me, on=["dataset", "carga_treino"], how="outer").sort_values(
        ["dataset", "carga_treino"]
    )
    merged["diferenca"] = (
        merged["aditivo_spearman"] - merged["multievolve_spearman"]
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out, sep="\t", index=False)

    print("== Spearman no teste: ridge ADITIVO vs MULTI-evolve (one-hot, Tabela S3) ==")
    print("   (particoes NAO identicas — leitura indicativa, ver docstring)\n")
    wide = merged.pivot_table(
        index="dataset",
        columns="carga_treino",
        values=["aditivo_spearman", "multievolve_spearman"],
    )
    print(wide.round(4).to_string())

    print("\n== media por carga de treino ==")
    print(
        merged.groupby("carga_treino")[
            ["aditivo_spearman", "multievolve_spearman", "diferenca"]
        ]
        .mean()
        .round(4)
        .to_string()
    )

    print("\n== celulas em que o ADITIVO iguala ou supera o MULTI-evolve ==")
    cmp_ok = merged.dropna(subset=["aditivo_spearman", "multievolve_spearman"])
    wins = cmp_ok[cmp_ok["diferenca"] >= 0]
    print(f"{len(wins)} de {len(cmp_ok)} celulas comparaveis")
    if len(wins):
        print(
            wins[["dataset", "carga_treino", "aditivo_spearman",
                  "multievolve_spearman", "diferenca"]]
            .round(4)
            .to_string(index=False)
        )

    print(f"\nescrito: {out}")


if __name__ == "__main__":
    main()
