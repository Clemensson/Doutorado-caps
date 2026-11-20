"""Inspeciona planilhas .xlsx: abas, dimensoes, colunas e primeiras linhas.

Uso:  python -I scripts/peek_xlsx.py <arquivo.xlsx> [...]

Dados de terceiros sao tratados como entrada: caminhos vem por argumento,
nada e importado de dentro do diretorio de dados.
"""

import sys

import pandas as pd


def peek(path: str, n_rows: int = 6, max_cols: int = 14) -> None:
    print("=" * 78)
    print(path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1])
    print("=" * 78)
    try:
        sheets = pd.read_excel(path, sheet_name=None, nrows=200)
    except Exception as exc:  # noqa: BLE001
        print(f"  !! falha ao ler: {exc}")
        return

    for name, df in sheets.items():
        print(f"\n-- aba: {name!r}  ({df.shape[0]}+ linhas lidas, {df.shape[1]} colunas)")
        cols = list(df.columns)
        shown = cols[:max_cols]
        print(f"   colunas: {shown}{' ...' if len(cols) > max_cols else ''}")
        with pd.option_context("display.width", 200, "display.max_columns", max_cols):
            print(df.iloc[:n_rows, :max_cols].to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("informe ao menos um arquivo .xlsx")
    for p in sys.argv[1:]:
        peek(p)
        print()
