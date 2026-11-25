"""O mapa de regimes: o NAC nas 15 celulas (5 conjuntos x 3 cargas de treino).

E a entrega (2) revisada do capitulo (ESPECIFICACAO.md secao 7.3). A pergunta que o
mapa responde:

    Em que regime o incremento de epistasia ESPECIFICA sobre um modelo de escala
    sobrevive a calibracao contra o nulo aditivo?

Duas quantidades por celula:

  efeito_pairwise    ganho do ridge com interacoes pareadas sobre o aditivo, menos a
                     mediana do nulo. Mede toda a estrutura nao aditiva que um modelo
                     de interacao captura.
  efeito_global      o mesmo para o modelo monotonico, que NAO pode representar
                     interacao. Mede so a parcela de escala.

  incremento = efeito_pairwise - efeito_global
                     o que sobra para interacao especifica depois de descontar a
                     escala. E o numero central do capitulo.

Uso:
    python -I papers/paper1-nulo-calibrado/src/analyze_nac_map.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

pd.set_option("display.width", 220)

ORDEM = ["ParD3", "GB1", "TrpB", "IGP dehydratase", "NucB"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nac-dir", default="resultados_hpc/nac")
    args = ap.parse_args()

    files = sorted(Path(args.nac_dir).glob("*.tsv"))
    d = pd.concat([pd.read_csv(f, sep="\t") for f in files], ignore_index=True)
    d = d[d["dataset"] != "dataset"]
    for c in ("ganho_observado", "ganho_nulo_mediana", "efeito_calibrado",
              "p_calibrado", "B"):
        d[c] = pd.to_numeric(d[c], errors="coerce")

    print("=" * 78)
    print("0. COBERTURA")
    print("=" * 78)
    print(f"arquivos: {len(files)}   linhas: {len(d)}")
    cob = d.pivot_table(index="dataset", columns="carga_treino",
                        values="efeito_calibrado", aggfunc="size")
    print("\ncelulas por conjunto e carga:")
    print(cob.to_string())
    print(f"\nB: {sorted(d.B.dropna().unique())}")
    print(f"politica de sigma: {sorted(d.sigma_unseen.dropna().unique())}")
    print(f"p calibrado minimo possivel: 1/(B+1) = {1 / (d.B.max() + 1):.4f}")

    # ---- o mapa ----
    piv = d.pivot_table(index=["dataset", "carga_treino"],
                        columns=["modelo", "metrica"],
                        values="efeito_calibrado")
    for met in ("pearson", "spearman"):
        print("\n" + "=" * 78)
        print(f"1. MAPA DE REGIMES — efeito calibrado, {met.upper()}")
        print("=" * 78)
        sub = d[(d.metrica == met) & (d.regime == "all")]
        t = sub.pivot_table(index="dataset", columns=["carga_treino", "modelo"],
                            values="efeito_calibrado")
        t = t.reindex([x for x in ORDEM if x in t.index])
        print(t.round(4).to_string())

    # ---- o incremento da interacao ----
    print("\n" + "=" * 78)
    print("2. O NUMERO CENTRAL: incremento da interacao especifica")
    print("=" * 78)
    print("incremento = efeito(pareado) - efeito(global). Positivo = o modelo que")
    print("pode representar interacao supera o que nao pode.\n")
    for met in ("pearson", "spearman"):
        sub = d[d.metrica == met]
        w = sub.pivot_table(index=["dataset", "carga_treino", "regime"],
                            columns="modelo", values="efeito_calibrado")
        if not {"pairwise", "global_iso"} <= set(w.columns):
            continue
        w["incremento"] = (w["pairwise"] - w["global_iso"]).round(4)
        for reg in ("all", "interpolacao", "extrapolacao"):
            r = w.xs(reg, level="regime")["incremento"].unstack("carga_treino")
            r = r.reindex([x for x in ORDEM if x in r.index])
            print(f"-- {met}, {reg} --")
            print(r.round(4).to_string())
            print()

    # ---- significancia ----
    print("=" * 78)
    print("3. QUANTAS CELULAS TEM EFEITO SIGNIFICATIVO")
    print("=" * 78)
    piso = 1 / (d.B.max() + 1)
    sig = d[d.p_calibrado <= piso * 1.01]
    tot = d.groupby(["modelo", "metrica", "regime"]).size().rename("celulas")
    nsig = sig.groupby(["modelo", "metrica", "regime"]).size().rename("no_piso")
    t = pd.concat([tot, nsig], axis=1).fillna(0).astype(int)
    t["fracao"] = (t.no_piso / t.celulas).round(2)
    print(f"('no piso' = p calibrado no minimo possivel, {piso:.4f})\n")
    print(t.to_string())

    print("\n" + "=" * 78)
    print("4. POR CARGA DE TREINO — media entre conjuntos")
    print("=" * 78)
    for met in ("pearson", "spearman"):
        sub = d[(d.metrica == met) & (d.regime == "all")]
        t = sub.pivot_table(index="carga_treino", columns="modelo",
                            values="efeito_calibrado")
        if {"pairwise", "global_iso"} <= set(t.columns):
            t["incremento"] = t["pairwise"] - t["global_iso"]
        print(f"-- {met} --")
        print(t.round(4).to_string())
        print()


if __name__ == "__main__":
    main()
