"""Analise 1 — os efeitos das mutacoes se somam? E, quando nao somam, de que forma?

A PERGUNTA, em linguagem simples. Se o efeito de cada mutacao fosse independente das
outras, o efeito de uma combinacao seria a SOMA dos efeitos individuais. Entao:
ajustamos um modelo que supoe exatamente isso, pedimos a ele uma previsao para cada
variante, e comparamos com o que foi medido.

    se os efeitos somam        a nuvem de pontos cola na diagonal
    se nao somam               a nuvem entorta, e a FORMA da entortada diz como

POR QUE ISTO IMPORTA ALEM DA EDA. A curva mediana observada contra a prevista e
literalmente a funcao que um modelo de epistasia global aprende. Nomear a forma dela
e a lacuna aberta do Artigo 1 (RESULTADOS_ESCALA.md secao 4): sabemos que nao e
censura e que so 15-26% e logaritmica, e o resto esta sem nome.

METODO. Ridge sobre a matriz indicadora de mutacoes (uma coluna por mutacao pontual
distinta), alfa escolhido por validacao cruzada de 3 pastas numa grade pequena. O
ajuste e DESCRITIVO, sobre todos os dados: a pergunta e a forma do sinal, nao
desempenho preditivo — e por isso nao ha particao de teste aqui. O intercepto do
ridge absorve o nivel do tipo selvagem, que varios conjuntos nao trazem como linha.

A matriz e mantida esparsa do inicio ao fim: densificar Phototropin (167 mil
variantes x 2.122 mutacoes) pediria 2,8 GB.

LEITURA DA ASSIMETRIA. Reportamos Pearson e Spearman da observacao contra a previsao.
Spearman e invariante a transformacao monotonica das previsoes; Pearson nao. Um
Spearman alto com Pearson baixo significa: o modelo aditivo acerta a ORDEM das
variantes e erra a ESCALA — ou seja, falta uma transformacao monotonica, nao
interacao entre mutacoes.

Uso:
    python -I exploratoria/src/analise1_curva_aditiva.py \\
        --data-dir data/external/zenodo-17620759 \\
        --out-res exploratoria/resultados --out-fig exploratoria/figuras
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import RidgeCV

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ALPHAS = np.logspace(-2, 3, 12)
N_FAIXAS = 24

SUP = "#ffffff"
AZ_200, AZ_450, AZ_700 = "#9dc8f7", "#257de0", "#0e3d7e"
TINTA, TINTA_FRACA, GRADE = "#1a1a1a", "#6b6b6b", "#e6e6e6"

ROTULO = {
    "HIS7_YEAST_Pokusaeva_2019": "IGP dehydratase",
    "TRPB1_THEMA_Tm9D8_Johnston_2024": "TrpB",
    "F7YBW8_MESOW_Aakre_2015": "ParD3", "SPG1_STRSG_Wu_2016": "GB1",
    "GFP_AEQVI_Sarkisyan_2016": "avGFP", "CAPSD_AAV2S_Sinai_2021": "AAV2 VP1",
    "VH14_Li_2023": "scFv", "Q8WTC7_9CNID_Somermeyer_2022": "amacGFP",
    "Q6WV13_9MAXI_Somermeyer_2022": "ppluGFP2",
    "D7PM05_CLYGR_Somermeyer_2022": "cgreGFP",
    "Q65J43_BACLD_g4_Thomas_2025": "NucB", "PHOT_CHLRE_Chen_2023": "Phototropin",
}
RECOMENDADOS = {"IGP dehydratase", "TrpB", "ParD3", "GB1"}


def ajusta(csv: Path):
    df = pd.read_csv(csv, usecols=["mutant", "DMS_score"]).dropna()
    toks = df["mutant"].astype(str).str.split(":")
    vocab = sorted({t for ts in toks for t in ts})
    idx = {m: j for j, m in enumerate(vocab)}
    linhas, cols = [], []
    for i, ts in enumerate(toks):
        for t in ts:
            linhas.append(i); cols.append(idx[t])
    X = sp.csr_matrix((np.ones(len(linhas)), (linhas, cols)),
                      shape=(len(df), len(vocab)))
    y = df["DMS_score"].to_numpy(float)
    mod = RidgeCV(alphas=ALPHAS, fit_intercept=True, cv=3).fit(X, y)
    return y, mod.predict(X), len(vocab)


def curva(y, pred):
    """Mediana observada por faixa de previsao — a forma, livre de ruido ponto a ponto."""
    bordas = np.quantile(pred, np.linspace(0, 1, N_FAIXAS + 1))
    bordas = np.unique(bordas)
    if len(bordas) < 4:
        return None
    faixa = np.clip(np.digitize(pred, bordas[1:-1]), 0, len(bordas) - 2)
    linhas = []
    for b in range(len(bordas) - 1):
        m = faixa == b
        if m.sum() < 20:
            continue
        linhas.append({"prev_mediana": float(np.median(pred[m])),
                       "obs_mediana": float(np.median(y[m])),
                       "obs_q1": float(np.quantile(y[m], .25)),
                       "obs_q3": float(np.quantile(y[m], .75)),
                       "n": int(m.sum())})
    return pd.DataFrame(linhas)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-res", required=True)
    ap.add_argument("--out-fig", required=True)
    args = ap.parse_args()
    res, figd = Path(args.out_res), Path(args.out_fig)

    resumo, curvas = [], []
    for csv in sorted(Path(args.data_dir).glob("*.csv")):
        nome = ROTULO.get(csv.name.removesuffix(".csv"), csv.name)
        y, pred, p = ajusta(csv)
        r = float(pearsonr(y, pred).statistic)
        rho = float(spearmanr(y, pred).statistic)
        cv = curva(y, pred)
        if cv is not None:
            cv.insert(0, "conjunto", nome)
            curvas.append(cv)
        resumo.append({"conjunto": nome, "n": len(y), "p_mutacoes": p,
                       "pearson": round(r, 4), "spearman": round(rho, 4),
                       "excesso_spearman": round(rho - r, 4)})
        print(f"  {nome:<17} n={len(y):>7} p={p:>5}  r={r:+.4f}  rho={rho:+.4f}  "
              f"rho-r={rho - r:+.4f}", flush=True)

    rs = pd.DataFrame(resumo).sort_values("excesso_spearman", ascending=False)
    rs.to_csv(res / "analise1_resumo.tsv", sep="\t", index=False)
    cs = pd.concat(curvas, ignore_index=True)
    cs.to_csv(res / "analise1_curvas.tsv", sep="\t", index=False)

    # ---- figura: pequenos multiplos da curva ----
    plt.rcParams.update({
        "figure.facecolor": SUP, "axes.facecolor": SUP,
        "font.family": "DejaVu Sans", "font.size": 9, "text.color": TINTA,
        "axes.edgecolor": GRADE, "grid.color": GRADE,
        "xtick.color": TINTA_FRACA, "ytick.color": TINTA_FRACA,
        "xtick.major.size": 0, "ytick.major.size": 0, "savefig.dpi": 200,
        "savefig.bbox": "tight"})
    nomes = sorted(cs.conjunto.unique())
    fig, axes = plt.subplots(3, 4, figsize=(11.5, 7.2))
    for ax, n in zip(axes.ravel(), nomes, strict=True):
        d = cs[cs.conjunto == n]
        lo = min(d.prev_mediana.min(), d.obs_mediana.min())
        hi = max(d.prev_mediana.max(), d.obs_mediana.max())
        ax.plot([lo, hi], [lo, hi], color=TINTA_FRACA, linewidth=1,
                linestyle=(0, (4, 3)), zorder=1)
        ax.fill_between(d.prev_mediana, d.obs_q1, d.obs_q3,
                        color=AZ_200, alpha=.55, linewidth=0, zorder=2)
        ax.plot(d.prev_mediana, d.obs_mediana, color=AZ_450, linewidth=2,
                marker="o", markersize=3.5, markeredgecolor=SUP,
                markeredgewidth=.8, zorder=3)
        dest = n in RECOMENDADOS
        ax.set_title(n, loc="left", fontsize=9.5, color=AZ_700 if dest else TINTA_FRACA,
                     fontweight="bold" if dest else "normal")
        ax.grid(alpha=.7); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(labelsize=7.5)
    fig.suptitle("Se os efeitos se somassem, a curva azul seguiria a linha tracejada",
                 x=0.012, ha="left", fontsize=13, fontweight="bold")
    fig.supxlabel("previsto por um modelo que SOMA os efeitos individuais",
                  fontsize=9.5, color=TINTA_FRACA)
    fig.supylabel("medido no experimento (mediana por faixa; faixa clara = quartis)",
                  fontsize=9.5, color=TINTA_FRACA)
    fig.tight_layout(rect=(0.02, 0.025, 1, 0.935))
    p1 = figd / "fig6_curva_aditiva.png"
    fig.savefig(p1); plt.close(fig)
    print(f"\n  {p1.name}")

    # ---- figura: a assimetria Pearson x Spearman ----
    fig, ax = plt.subplots(figsize=(8, 4.6))
    o = rs.sort_values("excesso_spearman")
    yy = range(len(o))
    for i, (_, r_) in zip(yy, o.iterrows(), strict=True):
        ax.plot([r_.pearson, r_.spearman], [i, i], color=GRADE, linewidth=3, zorder=1)
        ax.plot([r_.pearson], [i], "o", markersize=8, color=AZ_200,
                markeredgecolor=SUP, markeredgewidth=1.5, zorder=3)
        ax.plot([r_.spearman], [i], "o", markersize=8, color=AZ_700,
                markeredgecolor=SUP, markeredgewidth=1.5, zorder=3)
    ax.set_yticks(list(yy)); ax.set_yticklabels(o.conjunto)
    ax.set_xlabel("correlação entre o medido e o previsto pelo modelo aditivo",
                  color=TINTA_FRACA)
    ax.set_title("Onde o ponto escuro está à direita, o modelo aditivo acerta a ORDEM\n"
                 "e erra a ESCALA — falta uma transformação, não interação",
                 loc="left", fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="x"); ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.plot([], [], "o", color=AZ_200, label="Pearson (acerta a escala)")
    ax.plot([], [], "o", color=AZ_700, label="Spearman (acerta a ordem)")
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    p2 = figd / "fig7_assimetria.png"
    fig.savefig(p2); plt.close(fig)
    print(f"  {p2.name}")


if __name__ == "__main__":
    main()
