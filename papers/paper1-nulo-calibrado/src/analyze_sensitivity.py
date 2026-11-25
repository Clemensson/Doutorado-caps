"""Analise das duas sensibilidades pendentes: val_frac e fold_seed.

POR QUE ISTO IMPORTA. Todas as conclusoes do capitulo repousam em efeitos de 0,02 a
0,13 de correlacao. Duas escolhas nossas podiam estar sustentando esses numeros:

  val_frac   O early stopping exige conjunto de validacao, mas o val_split usado por
             Tran et al. NAO esta documentado em nenhuma das tres fontes. Adotamos
             10%. Se a conclusao mudar com 5% ou 20%, ela e artefato da nossa
             escolha.

  fold_seed  Toda a analise usou uma unica semente de particionamento (42). A
             dispersao entre sementes E A VARIABILIDADE AMOSTRAL contra a qual os
             efeitos precisam ser julgados. Sem ela, nao se sabe se +0,02 e sinal ou
             ruido de particionamento.

O baseline (val_frac=0,10, fold_seed=42) vem de fcnn_resultados/merged.tsv.

Cada arquivo contem FCNN e aditivo ajustados nos MESMOS folds, portanto o delta e
pareado dentro do arquivo — trocar a semente muda os dois modelos junto, que e o
comportamento correto.

Uso:
    python -I papers/paper1-nulo-calibrado/src/analyze_sensitivity.py
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.width", 220)

# ATENCAO: a chave do pareamento NAO inclui 'featurizacao'. O run_one.py grava as
# linhas do aditivo sempre com featurizacao='mut', porque o aditivo nao usa one-hot
# de sequencia. Incluir a coluna na chave faz os arquivos 'seq' nao encontrarem par
# e serem descartados em silencio — metade dos dados desaparece sem erro.
KEY = ["dataset", "carga_treino", "carga_teste"]


def deltas(df: pd.DataFrame) -> pd.DataFrame:
    """FCNN menos aditivo, pareado dentro do arquivo. Positivo = FCNN melhor."""
    fc = df[df["modelo"] == "fcnn"]
    ad = df[df["modelo"] == "additive"].drop_duplicates(subset=KEY)
    m = fc.merge(ad[KEY + ["pearson", "spearman"]], on=KEY,
                 suffixes=("", "_ad"), how="inner")
    if len(m) != len(fc):
        raise RuntimeError(
            f"pareamento perdeu linhas: {len(fc)} da FCNN -> {len(m)} pareadas")
    m["d_pearson"] = m["pearson"] - m["pearson_ad"]
    m["d_spearman"] = m["spearman"] - m["spearman_ad"]
    pl = m[m["carga_teste"] != "all"].copy()
    pl["ct"] = pl["carga_teste"].astype(int)
    pl["regime"] = np.where(pl["ct"] <= pl["carga_treino"],
                            "interpolacao", "extrapolacao")
    return pl


def media_por_conjunto(g: pd.DataFrame, col: str) -> float:
    """Media das celulas dentro de cada conjunto, depois media entre conjuntos.

    O conjunto e a unidade de analise do capitulo: celulas do mesmo conjunto
    compartilham folds e coeficientes, portanto nao sao independentes.
    """
    return float(g.groupby("dataset")[col].mean().mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sens-dir", default="resultados_hpc/sens")
    ap.add_argument("--baseline", default="fcnn_resultados/merged.tsv")
    args = ap.parse_args()

    base = pd.read_csv(args.baseline, sep="\t")
    base["carga_teste"] = base["carga_teste"].astype(str)
    base_pl = deltas(base)
    base_pl["val_frac"], base_pl["fold_seed"] = 0.10, 42

    rows = []
    pat = re.compile(r"_(val_frac|fold_seed)_vf([\d.]+)_fs(\d+)\.tsv$")
    for p in sorted(Path(args.sens_dir).glob("*.tsv")):
        mm = pat.search(p.name)
        if not mm:
            continue
        d = pd.read_csv(p, sep="\t")
        d["carga_teste"] = d["carga_teste"].astype(str)
        pl = deltas(d)
        pl["val_frac"] = float(mm.group(2))
        pl["fold_seed"] = int(mm.group(3))
        rows.append(pl)
    todos = pd.concat([base_pl] + rows, ignore_index=True)

    print("=" * 78)
    print("0. COBERTURA")
    print("=" * 78)
    print(f"linhas: {len(todos)}   conjuntos: {todos.dataset.nunique()}")
    print(f"val_frac: {sorted(todos.val_frac.unique())}")
    print(f"fold_seed: {sorted(todos.fold_seed.unique())}")

    # ---------------- val_frac ----------------
    print("\n" + "=" * 78)
    print("1. SENSIBILIDADE A val_frac  (fold_seed = 42)")
    print("=" * 78)
    print("Delta = FCNN - aditivo. Positivo = a rede melhor.\n")
    vf = todos[todos.fold_seed == 42]
    for col, met in (("d_pearson", "pearson"), ("d_spearman", "spearman")):
        t = (vf.groupby(["featurizacao", "regime", "val_frac"])
             .apply(lambda g, c=col: media_por_conjunto(g, c), include_groups=False)
             .unstack("val_frac"))
        t["amplitude"] = (t.max(axis=1) - t.min(axis=1)).round(4)
        print(f"-- {met} --")
        print(t.round(4).to_string())
        print()

    # ---------------- fold_seed ----------------
    print("=" * 78)
    print("2. VARIABILIDADE ENTRE SEMENTES DE FOLD  (val_frac = 0,10)")
    print("=" * 78)
    print("O desvio-padrao entre sementes e a regua: um efeito menor que ele nao e")
    print("distinguivel de ruido de particionamento.\n")
    fs = todos[todos.val_frac == 0.10]
    for col, met in (("d_pearson", "pearson"), ("d_spearman", "spearman")):
        per = (fs.groupby(["featurizacao", "regime", "fold_seed"])
               .apply(lambda g, c=col: media_por_conjunto(g, c),
                      include_groups=False)
               .rename("delta").reset_index())
        t = per.pivot_table(index=["featurizacao", "regime"],
                            columns="fold_seed", values="delta")
        t["media"] = t.mean(axis=1).round(4)
        t["desvio"] = t[[c for c in t.columns if isinstance(c, int)]].std(axis=1).round(4)
        t["amplitude"] = (t[[c for c in t.columns if isinstance(c, int)]].max(axis=1)
                          - t[[c for c in t.columns if isinstance(c, int)]].min(axis=1)).round(4)
        print(f"-- {met} --")
        print(t.round(4).to_string())
        print()

    # ---------------- o teste que importa ----------------
    print("=" * 78)
    print("3. OS EFEITOS DO CAPITULO CONTRA A REGUA DAS SEMENTES")
    print("=" * 78)
    alvos = [
        ("seq", "extrapolacao", "d_spearman",
         "aditivo melhor na extrapolacao (sinal invertido)"),
        ("mut", "interpolacao", "d_pearson", "vantagem da FCNN em Pearson"),
        ("seq", "interpolacao", "d_pearson", "vantagem da FCNN em Pearson"),
        ("mut", "interpolacao", "d_spearman", "vantagem da FCNN em Spearman"),
        ("seq", "interpolacao", "d_spearman", "vantagem da FCNN em Spearman"),
    ]
    out = []
    for feat, reg, col, rotulo in alvos:
        sub = fs[(fs.featurizacao == feat) & (fs.regime == reg)]
        per = sub.groupby("fold_seed").apply(
            lambda g, c=col: g.groupby("dataset")[c].mean().mean(),
            include_groups=False)
        per.index = per.index.astype(int)
        b = float(per.loc[42]) if 42 in per.index else float("nan")
        sd = float(per.std())
        out.append({
            "featurizacao": feat, "regime": reg,
            "metrica": col.replace("d_", ""), "o_que": rotulo,
            "baseline_fs42": round(b, 4),
            "media_5_sementes": round(float(per.mean()), 4),
            "desvio_sementes": round(sd, 4),
            "efeito_sobre_desvio": (round(abs(float(per.mean())) / sd, 1)
                                    if sd > 0 else float("inf")),
        })
    print(pd.DataFrame(out).to_string(index=False))
    print("\n'efeito_sobre_desvio' < 1 significa que o efeito e menor que a")
    print("variabilidade de particionamento, logo nao sustentavel.")


if __name__ == "__main__":
    main()
