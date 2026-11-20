"""Resume as Tabelas S3 e S4 do suplementar de Tran et al.

Uso:  python -I scripts/summarize_s3_s4.py <S3.xlsx> <S4.xlsx>
"""

import sys

import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 120)


def main(s3_path: str, s4_path: str) -> None:
    s3 = pd.read_excel(s3_path)
    print("=" * 78)
    print("TABELA S3 — composicao de treino e encodings")
    print("=" * 78)
    print(f"linhas: {len(s3)}")
    print(f"\nFeatures testadas ({s3['Feature'].nunique()}):")
    for f in sorted(s3["Feature"].dropna().unique()):
        print(f"  - {f}")
    print(f"\nCargas de treino: {sorted(s3['Training Load'].dropna().unique())}")
    print(f"\nConjuntos ({s3['Dataset Name'].nunique()}):")
    for d in sorted(s3["Dataset Name"].dropna().unique()):
        print(f"  - {d}")

    print("\n-- Spearman-Test medio por feature e carga de treino --")
    piv = s3.pivot_table(
        index="Feature", columns="Training Load", values="Spearman - Test", aggfunc="mean"
    )
    print(piv.round(4).to_string())

    print("\n-- Spearman-Test medio por conjunto e carga --")
    piv2 = s3.pivot_table(
        index="Dataset Name", columns="Training Load", values="Spearman - Test", aggfunc="mean"
    )
    print(piv2.round(4).to_string())

    s4 = pd.read_excel(s4_path, sheet_name=None)
    print("\n" + "=" * 78)
    print("TABELA S4 — split por carga mutacional")
    print("=" * 78)
    for name, df in s4.items():
        print(f"\n-- aba {name!r}: {df.shape[0]} linhas x {df.shape[1]} colunas")
        print(f"   colunas: {list(df.columns)}")
        print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
