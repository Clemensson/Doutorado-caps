"""Figuras didaticas do relatorio de EDA.

Segue o procedimento da skill `dataviz`, na ordem: forma primeiro, cor pela funcao
que exerce, especificacao de marca, acessibilidade.

PALETA. Usamos a paleta de referencia de `references/palette.md` LITERALMENTE, sem
inventar cores. A skill a declara como instancia validada, o que dispensa nova
validacao — necessario porque `scripts/validate_palette.js` precisa de Node, que nao
esta instalado nesta maquina.

    superficie clara  #ffffff
    rampa sequencial azul  100 #cce3fd  200 #9dc8f7  450 #257de0  700 #0e3d7e

DESVIOS DECLARADOS. Duas etapas do procedimento nao se aplicam a um PDF estatico:

    passo 5 (camada de hover)  — PDF impresso nao tem interacao
    passo 6 (modo escuro)      — PDF impresso nao tem tema

A exigencia de "table view" do passo 6 e satisfeita pelas tabelas do relatorio e
pelos TSV em exploratoria/resultados/.

COR COMO ENFASE, NAO COMO MAGNITUDE. Nas figuras de barras a propria barra ja
codifica magnitude, portanto colorir por valor seria redundante. Usamos dois passos
de UMA hue (claro para o conjunto comum, escuro para o recomendado) como enfase
binaria, e a identidade vem sempre do rotulo direto — nunca da cor sozinha.

Uso:
    python -I exploratoria/src/figuras.py --res exploratoria/resultados \
        --out exploratoria/figuras
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# --- paleta de referencia da skill dataviz, valores literais ---
SUP = "#ffffff"
AZ_100, AZ_200, AZ_450, AZ_700 = "#cce3fd", "#9dc8f7", "#257de0", "#0e3d7e"
TINTA = "#1a1a1a"
TINTA_FRACA = "#6b6b6b"
GRADE = "#e6e6e6"

RECOMENDADOS = {"HIS7_YEAST_Pokusaeva_2019", "TRPB1_THEMA_Tm9D8_Johnston_2024",
                "F7YBW8_MESOW_Aakre_2015", "SPG1_STRSG_Wu_2016"}

ROTULO = {
    "HIS7_YEAST_Pokusaeva_2019": "IGP dehydratase",
    "TRPB1_THEMA_Tm9D8_Johnston_2024": "TrpB",
    "F7YBW8_MESOW_Aakre_2015": "ParD3",
    "SPG1_STRSG_Wu_2016": "GB1",
    "GFP_AEQVI_Sarkisyan_2016": "avGFP",
    "CAPSD_AAV2S_Sinai_2021": "AAV2 VP1",
    "VH14_Li_2023": "scFv",
    "Q8WTC7_9CNID_Somermeyer_2022": "amacGFP",
    "Q6WV13_9MAXI_Somermeyer_2022": "ppluGFP2",
    "D7PM05_CLYGR_Somermeyer_2022": "cgreGFP",
    "Q65J43_BACLD_g4_Thomas_2025": "NucB",
    "PHOT_CHLRE_Chen_2023": "Phototropin",
}


def estilo() -> None:
    plt.rcParams.update({
        "figure.facecolor": SUP, "axes.facecolor": SUP,
        "font.family": "DejaVu Sans", "font.size": 10,
        "text.color": TINTA, "axes.labelcolor": TINTA,
        "xtick.color": TINTA_FRACA, "ytick.color": TINTA,
        "axes.edgecolor": GRADE, "axes.linewidth": 1.0,
        "grid.color": GRADE, "grid.linewidth": 1.0,
        "xtick.major.size": 0, "ytick.major.size": 0,
        "savefig.dpi": 200, "savefig.bbox": "tight",
    })


def barras(ax, nomes, vals, fmt, titulo, xlabel, destaque=True):
    """Barra horizontal ordenada: a forma para magnitude entre categorias."""
    cores = [AZ_700 if (destaque and n in RECOMENDADOS) else AZ_200 for n in nomes]
    y = range(len(nomes))
    ax.barh(list(y), vals, color=cores, height=0.62,
            edgecolor=SUP, linewidth=2)  # 2px de folga entre barras
    ax.set_yticks(list(y))
    ax.set_yticklabels([ROTULO.get(n, n) for n in nomes])
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, color=TINTA_FRACA)
    ax.set_title(titulo, loc="left", fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    vmax = max(vals) if max(vals) > 0 else 1
    for i, v in zip(y, vals, strict=True):
        ax.text(v + vmax * 0.015, i, fmt(v), va="center", fontsize=9, color=TINTA)
    ax.set_xlim(0, vmax * 1.18)


def fig_piso(res: Path, out: Path) -> str:
    o = pd.read_csv(res / "eda_por_ordem.tsv", sep="\t")
    g = o.groupby("conjunto").apply(
        lambda d: (d.frac_no_piso * d.n).sum() / d.n.sum(), include_groups=False)
    g = g.sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    barras(ax, list(g.index), [v * 100 for v in g.values],
           lambda v: f"{v:.1f}%",
           "A maioria das variantes está no piso do ensaio em 5 conjuntos",
           "variantes no valor mínimo do conjunto (%)")
    p = out / "fig1_massa_no_piso.png"
    fig.savefig(p); plt.close(fig)
    return p.name


def fig_decomponibilidade(res: Path, out: Path) -> str:
    e = pd.read_csv(res / "eda_epistasia.tsv", sep="\t")
    e = e.sort_values("frac_sem_todos_singles", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    barras(ax, list(e.conjunto), [v * 100 for v in e.frac_sem_todos_singles],
           lambda v: f"{v:.1f}%",
           "Em NucB e scFv, quase nenhum multimutante pode ser decomposto",
           "multimutantes sem todas as mutações isoladas medidas (%)")
    p = out / "fig2_decomponibilidade.png"
    fig.savefig(p); plt.close(fig)
    return p.name


def fig_candidatos(res: Path, out: Path) -> str:
    e = pd.read_csv(res / "eda_epistasia.tsv", sep="\t").fillna({"n_compensatorio": 0})
    e = e.sort_values("n_compensatorio", ascending=False)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    barras(axes[0], list(e.conjunto), list(e.n_compensatorio),
           lambda v: f"{int(v)}",
           "Quantos candidatos existem", "candidatos (contagem)")
    e2 = e.sort_values("frac_compensatorio", ascending=False)
    barras(axes[1], list(e2.conjunto), [v * 100 for v in e2.frac_compensatorio],
           lambda v: f"{v:.2f}%",
           "Qual a taxa", "candidatos entre os decomponíveis (%)")
    fig.suptitle("O sinal compensatório é raro: no melhor caso, 0,73% das combinações",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    p = out / "fig3_candidatos.png"
    fig.savefig(p); plt.close(fig)
    return p.name


def fig_score_ordem(res: Path, out: Path) -> str:
    """Pequenos multiplos: a forma para 12 entidades com a mesma relacao."""
    o = pd.read_csv(res / "eda_por_ordem.tsv", sep="\t")
    cors = pd.read_csv(res / "eda_correlacoes.tsv", sep="\t").set_index("conjunto")
    nomes = sorted(o.conjunto.unique(), key=lambda n: ROTULO.get(n, n))
    fig, axes = plt.subplots(3, 4, figsize=(11, 6.6), sharex=False)
    for ax, n in zip(axes.ravel(), nomes, strict=True):
        d = o[o.conjunto == n].sort_values("ordem")
        ax.plot(d.ordem, d.mediana, color=AZ_450, linewidth=2,
                marker="o", markersize=4, markeredgecolor=SUP, markeredgewidth=1)
        r = cors.loc[n, "spearman_score_vs_ordem"]
        destaque = AZ_700 if n in RECOMENDADOS else TINTA_FRACA
        ax.set_title(f"{ROTULO.get(n, n)}   ρ={r:+.2f}", loc="left",
                     fontsize=9.5, color=destaque,
                     fontweight="bold" if n in RECOMENDADOS else "normal")
        ax.grid(axis="y"); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(labelsize=8)
    fig.suptitle("O fenótipo cai com o número de mutações — exceto em scFv, "
                 "onde sobe (ρ=+0,67)", x=0.01, ha="left",
                 fontsize=12, fontweight="bold")
    fig.supxlabel("número de mutações na variante", fontsize=9, color=TINTA_FRACA)
    # Cada painel tem escala propria: o score nao e comparavel entre conjuntos
    # (ver fig5). O que se le aqui e a FORMA da curva, nao o nivel.
    fig.supylabel("mediana do score — cada painel em sua própria escala",
                  fontsize=9, color=TINTA_FRACA)
    fig.tight_layout(rect=(0.02, 0.02, 1, 0.93))
    p = out / "fig4_score_vs_ordem.png"
    fig.savefig(p); plt.close(fig)
    return p.name


def fig_escalas(res: Path, out: Path) -> str:
    """Pontos, NAO barras.

    Barra codifica magnitude a partir do zero, e escala logaritmica nao tem zero —
    o comprimento da barra ficaria arbitrario, definido pelo limite inferior do eixo.
    Ponto nao reivindica linha de base, entao e a marca correta aqui.

    O NucB tem IQR EXATAMENTE 0, que nao e representavel em log. Entra como anotacao
    explicita em vez de ser recortado para um valor pequeno — recortar seria inventar
    um numero que o dado nao tem.
    """
    c = pd.read_csv(res / "eda_colunas.tsv", sep="	")
    s = c[c.coluna == "DMS_score"].copy().sort_values("iqr", ascending=False)
    zero = s[s.iqr <= 0]
    pos = s[s.iqr > 0]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    nomes = list(pos.conjunto) + list(zero.conjunto)
    y = list(range(len(nomes)))
    for i, (n, v) in enumerate(zip(pos.conjunto, pos.iqr, strict=True)):
        cor = AZ_700 if n in RECOMENDADOS else AZ_450
        ax.plot([v], [i], marker="o", markersize=9, color=cor,
                markeredgecolor=SUP, markeredgewidth=2, zorder=3)
        ax.text(v * 1.35, i, f"{v:,.4g}".replace(",", "."), va="center",
                fontsize=9, color=TINTA)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([ROTULO.get(n, n) for n in nomes])
    ax.invert_yaxis()
    lo = float(pos.iqr.min()) / 4
    hi = float(pos.iqr.max()) * 20
    ax.set_xlim(lo, hi)
    # folga vertical para a anotacao do IQR=0 nao colidir com os rotulos do eixo x
    ax.set_ylim(len(nomes) - 0.25, -0.75)
    for i in range(len(pos), len(nomes)):
        ax.annotate("IQR = 0 exato — não representável em escala logarítmica",
                    xy=(lo * 1.6, i), va="center", fontsize=9, style="italic",
                    color=TINTA_FRACA)
    ax.set_xlabel("amplitude interquartil do score — ESCALA LOGARÍTMICA",
                  color=TINTA_FRACA)
    ax.set_title("As escalas diferem por seis ordens de magnitude: nenhum modelo "
                 "pode treinar nos 12 sem normalização por conjunto",
                 loc="left", fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="x"); ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    p = out / "fig5_escalas.png"
    fig.savefig(p); plt.close(fig)
    return p.name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res, out = Path(args.res), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    estilo()
    for fn in (fig_piso, fig_decomponibilidade, fig_candidatos,
               fig_score_ordem, fig_escalas):
        print(f"  {fn(res, out)}")


if __name__ == "__main__":
    main()
