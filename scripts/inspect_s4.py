"""Mapeia a estrutura da Tabela S4 (split por carga mutacional) de Tran et al.

Precisamos saber exatamente qual grade (carga de treino x carga de teste) foi
avaliada, para quais metodos e conjuntos, antes de replicar as particoes.

Uso:  python -I scripts/inspect_s4.py <S4.xlsx>
"""

import sys

import pandas as pd

pd.set_option("display.width", 220)
pd.set_option("display.max_rows", 300)
pd.set_option("display.max_columns", 40)


def main(path: str) -> None:
    df = pd.read_excel(path)
    print(f"linhas: {len(df)}   colunas: {list(df.columns)}\n")

    tr = "Max mutational load of train set"
    te = "Mutational load of test set"

    print("== Metodos ==")
    for m, c in df["Method"].value_counts().items():
        print(f"  {m!r}: {c} linhas")

    print("\n== Conjuntos ==")
    for d, c in df["Dataset Name"].value_counts().sort_index().items():
        print(f"  {d}: {c} linhas")

    print(f"\n== Cargas de treino presentes: {sorted(df[tr].dropna().unique())}")
    print(f"== Cargas de teste presentes: {sorted(df[te].dropna().unique(), key=str)}")

    print("\n== Grade treino x teste (contagem de linhas) ==")
    print(pd.crosstab(df[tr], df[te]).to_string())

    print("\n== Grade por conjunto: cargas de teste por carga de treino ==")
    for d, g in df.groupby("Dataset Name"):
        combos = sorted({(int(a), str(b)) for a, b in zip(g[tr], g[te], strict=True)})
        loads = sorted({a for a, _ in combos})
        print(f"\n  {d}  (treino: {loads})")
        for L in loads:
            tests = sorted(
                {b for a, b in combos if a == L},
                key=lambda s: (not str(s).isdigit(), int(s) if str(s).isdigit() else s),
            )
            print(f"     treino<={L}: teste={tests}")

    print("\n== Amostra completa de um conjunto pequeno (ParD3) ==")
    sub = df[df["Dataset Name"] == "ParD3"].sort_values(["Method", tr, te])
    print(sub.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1])
