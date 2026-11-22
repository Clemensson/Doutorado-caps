"""Confronta o baseline de epistasia global com a FCNN.

A pergunta do capitulo: que fracao da vantagem da FCNN sobre o ridge aditivo um
modelo SEM NENHUMA capacidade de interacao consegue recuperar?

Se a resposta for "a maior parte", a atribuicao do desempenho da FCNN a aprendizado
de epistasia fica insustentavel — o que ela adquire e escala, nao interacao.

Unidade de analise: o CONJUNTO (n=12). Celulas de um mesmo conjunto compartilham
folds e coeficientes, portanto nao sao independentes.

Uso:
    python -I papers/paper1-nulo-calibrado/src/compare_global_vs_fcnn.py \
        --global papers/paper1-nulo-calibrado/results/global_epistasis.tsv \
        --fcnn fcnn_resultados/merged.tsv
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

KEY = ["dataset", "carga_treino", "carga_teste"]


def ci(s: pd.Series) -> str:
    return f"[{s.mean() - 1.96 * s.sem():+.4f}, {s.mean() + 1.96 * s.sem():+.4f}]"


def wp(s: pd.Series) -> float:
    return wilcoxon(s).pvalue if len(s) >= 6 and s.std() > 0 else np.nan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--global", dest="glob", required=True)
    ap.add_argument("--fcnn", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    g = pd.read_csv(args.glob, sep="\t")
    g["carga_teste"] = g["carga_teste"].astype(str)
    f = pd.read_csv(args.fcnn, sep="\t")
    f["carga_teste"] = f["carga_teste"].astype(str)

    # Pivot: uma coluna por modelo
    parts = []
    for mod, lab in (("additive", "add"), ("global_iso", "giso"),
                     ("global_joint", "gjoint")):
        sub = g[g["modelo"] == mod][KEY + ["pearson", "spearman"]]
        parts.append(sub.rename(columns={"pearson": f"r_{lab}",
                                         "spearman": f"rho_{lab}"}))
    for feat, lab in (("mut", "fcmut"), ("seq", "fcseq")):
        sub = f[(f["modelo"] == "fcnn") & (f["featurizacao"] == feat)][
            KEY + ["pearson", "spearman"]]
        parts.append(sub.rename(columns={"pearson": f"r_{lab}",
                                         "spearman": f"rho_{lab}"}))

    m = parts[0]
    for p in parts[1:]:
        m = m.merge(p, on=KEY, how="inner")

    # sanity: o aditivo deste modulo deve coincidir com o do merged.tsv
    add_f = f[f["modelo"] == "additive"][KEY + ["pearson"]].drop_duplicates(
        subset=KEY).rename(columns={"pearson": "r_add_hpc"})
    chk = m.merge(add_f, on=KEY, how="inner")
    dmax = float((chk["r_add"] - chk["r_add_hpc"]).abs().max())
    print("=" * 78)
    print("0. CONSISTENCIA")
    print("=" * 78)
    print(f"celulas comparaveis: {len(m)}")
    print(f"desvio maximo do aditivo entre este modulo e o HPC: {dmax:.2e}")
    print("  (cargas 2-3 devem bater a ~1e-12; a carga 1 e subdeterminada e pode "
          "divergir — ver RESULTADOS_FCNN.md secao 6)")
    d1 = float((chk[chk.carga_treino == 1]["r_add"]
                - chk[chk.carga_treino == 1]["r_add_hpc"]).abs().max())
    d23 = float((chk[chk.carga_treino > 1]["r_add"]
                 - chk[chk.carga_treino > 1]["r_add_hpc"]).abs().max())
    print(f"  carga 1: {d1:.2e}   cargas 2-3: {d23:.2e}")

    per_load = m[m["carga_teste"] != "all"].copy()
    per_load["ct"] = per_load["carga_teste"].astype(int)
    per_load["regime"] = np.where(
        per_load["ct"] <= per_load["carga_treino"], "interpolacao", "extrapolacao")

    print("\n" + "=" * 78)
    print("1. GANHO EM PEARSON SOBRE O ADITIVO (unidade = conjunto, n=12)")
    print("=" * 78)
    print("Positivo = o modelo supera o ridge aditivo puro.\n")
    rows = []
    for regime in ("extrapolacao", "interpolacao"):
        sub = per_load[per_load["regime"] == regime]
        for lab, nome in (("giso", "global 2 estagios"),
                          ("gjoint", "global conjunto"),
                          ("fcmut", "FCNN (mut)"),
                          ("fcseq", "FCNN (seq)")):
            gain = (sub.groupby("dataset")
                    .apply(lambda t, l=lab: (t[f"r_{l}"] - t["r_add"]).mean(),
                           include_groups=False))
            rows.append({"regime": regime, "modelo": nome,
                         "ganho_pearson": round(gain.mean(), 4),
                         "ic95": ci(gain),
                         "melhor_que_aditivo": f"{int((gain > 0).sum())}/{len(gain)}",
                         "p_wilcoxon": round(wp(gain), 4)})
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n" + "=" * 78)
    print("2. GANHO EM SPEARMAN SOBRE O ADITIVO")
    print("=" * 78)
    print("Spearman e invariante a transformacao monotonica das predicoes, logo o")
    print("modelo de 2 estagios NAO deveria ganhar aqui (so perde pelos empates")
    print("que os patamares da isotonica criam). O conjunto muda beta e pode ganhar.\n")
    rows = []
    for regime in ("extrapolacao", "interpolacao"):
        sub = per_load[per_load["regime"] == regime]
        for lab, nome in (("giso", "global 2 estagios"),
                          ("gjoint", "global conjunto"),
                          ("fcmut", "FCNN (mut)"),
                          ("fcseq", "FCNN (seq)")):
            gain = (sub.groupby("dataset")
                    .apply(lambda t, l=lab: (t[f"rho_{l}"] - t["rho_add"]).mean(),
                           include_groups=False))
            rows.append({"regime": regime, "modelo": nome,
                         "ganho_spearman": round(gain.mean(), 4),
                         "ic95": ci(gain),
                         "melhor_que_aditivo": f"{int((gain > 0).sum())}/{len(gain)}",
                         "p_wilcoxon": round(wp(gain), 4)})
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n" + "=" * 78)
    print("3. O TESTE DIRETO: global vs FCNN")
    print("=" * 78)
    print("Delta positivo = o modelo SEM INTERACAO supera a FCNN.\n")
    rows = []
    for regime in ("extrapolacao", "interpolacao"):
        sub = per_load[per_load["regime"] == regime]
        for gl in ("giso", "gjoint"):
            for fcl in ("fcmut", "fcseq"):
                for met, pre in (("pearson", "r"), ("spearman", "rho")):
                    d = (sub.groupby("dataset")
                         .apply(lambda t, a=f"{pre}_{gl}", b=f"{pre}_{fcl}":
                                (t[a] - t[b]).mean(), include_groups=False))
                    rows.append({
                        "regime": regime,
                        "global": "2est" if gl == "giso" else "conj",
                        "fcnn": fcl.replace("fc", ""),
                        "metrica": met,
                        "delta": round(d.mean(), 4),
                        "ic95": ci(d),
                        "global_melhor": f"{int((d > 0).sum())}/{len(d)}",
                        "p_wilcoxon": round(wp(d), 4)})
    res = pd.DataFrame(rows)
    for met in ("pearson", "spearman"):
        print(f"-- {met} --")
        print(res[res.metrica == met].drop(columns="metrica").to_string(index=False))
        print()

    print("=" * 78)
    print("4. FRACAO DA VANTAGEM DA FCNN RECUPERADA (em Pearson)")
    print("=" * 78)
    print("Razao entre o ganho medio do modelo global e o da FCNN, por regime.")
    print("Calculada sobre as medias agregadas, nao como razao por celula, para")
    print("nao explodir quando o denominador e proximo de zero.\n")
    for regime in ("extrapolacao", "interpolacao"):
        sub = per_load[per_load["regime"] == regime]
        base = sub["r_add"].mean()
        for fcl, fnome in (("fcmut", "FCNN mut"), ("fcseq", "FCNN seq")):
            fc_gain = (sub[f"r_{fcl}"] - sub["r_add"]).mean()
            for gl, gnome in (("giso", "2 estagios"), ("gjoint", "conjunto")):
                g_gain = (sub[f"r_{gl}"] - sub["r_add"]).mean()
                frac = (g_gain / fc_gain) if abs(fc_gain) > 1e-9 else np.nan
                print(f"  {regime:<13} {gnome:<11} vs {fnome:<9} "
                      f"ganho global {g_gain:+.4f}  ganho FCNN {fc_gain:+.4f}  "
                      f"recuperado {frac * 100 if frac == frac else float('nan'):.0f}%")

    print("\n" + "=" * 78)
    print("5. TRUNCAMENTO DA NAO LINEARIDADE")
    print("=" * 78)
    print("g e aprendida so na faixa de x'beta do treino; variantes de teste fora")
    print("dela sao truncadas. Limita o que o modelo global pode recuperar na")
    print("extrapolacao.\n")
    tr = g[g["modelo"].isin(["global_iso", "global_joint"])]
    print(tr.groupby(["modelo", "carga_treino"])["frac_truncada"]
          .agg(["mean", "max"]).round(4).to_string())

    print("\n== por conjunto, Pearson na avaliacao global ('all') ==")
    glob = m[m["carga_teste"] == "all"]
    piv = glob.pivot_table(index="dataset", columns="carga_treino",
                           values=["r_add", "r_gjoint", "r_fcmut"])
    print(piv.round(3).to_string())

    if args.out:
        m.to_csv(args.out, sep="\t", index=False)
        print(f"\nescrito: {args.out}")


if __name__ == "__main__":
    main()
