"""Extrai celulas de codigo de um notebook .ipynb, opcionalmente filtrando por termo.

Uso:  python -I scripts/extract_nb_code.py <notebook.ipynb> [termo] [--full]

Sem termo, lista um indice das celulas de codigo. Com termo, imprime as celulas
que o contenham. Saidas das celulas sao ignoradas (sao grandes e nao interessam).
"""

import json
import sys
from pathlib import Path


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--full"]
    full = "--full" in sys.argv
    nb_path = Path(args[0])
    term = args[1] if len(args) > 1 else None

    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]

    if term is None:
        print(f"{nb_path.name}: {len(cells)} celulas de codigo\n")
        for i, c in enumerate(cells):
            src = "".join(c.get("source", []))
            first = next((ln for ln in src.splitlines() if ln.strip()), "")
            print(f"[{i:>3}] {len(src):>6} car  {first[:100]}")
        return

    hits = 0
    for i, c in enumerate(cells):
        src = "".join(c.get("source", []))
        if term.lower() in src.lower():
            hits += 1
            print("=" * 78)
            print(f"CELULA {i}")
            print("=" * 78)
            print(src if full else src[:4000])
            print()
    print(f"-- {hits} celulas contendo {term!r}")


if __name__ == "__main__":
    main()
