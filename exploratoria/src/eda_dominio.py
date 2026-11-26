"""Camada de dominio da EDA: o que a skill generica nao computa.

A skill `exploratory-data-analysis` entrega o perfil generico — ausencias, tipos,
cardinalidade, agregados, duplicatas — mas (a) seus quantis vem de uma subamostra de
512 elementos e (b) ela nao sabe o que e uma mutacao. Este modulo computa, sobre os
dados COMPLETOS, o que a equipe precisa para decidir como modelar.

PERGUNTA DE NEGOCIO: epistasia compensatoria — combinacoes em que mutacoes
individualmente neutras ou deleterias produzem uma variante melhor que as partes.
Toda secao abaixo existe para dizer se e onde os dados sustentam essa pergunta.

DEFINICOES OPERACIONAIS, declaradas porque nao sao padrao:

  supera_as_partes   multimutante cujo score excede o MAIOR score entre seus singles
                     constituintes. E a assinatura minima de epistasia positiva e NAO
                     exige referencia de tipo selvagem, que nem todo conjunto tem.

  compensatorio      multimutante em que TODOS os singles constituintes ficam abaixo
                     da mediana dos singles (individualmente neutros ou deleterios) E
                     o score da combinacao fica no decil superior do conjunto. E a
                     leitura estrita de "individualmente ruins, juntos bons".

Ambas exigem que todos os singles constituintes tenham sido medidos. A fracao de
multimutantes em que isso falha e reportada — e o custo do filtro de estringencia.

CONTRATO: dados brutos somente leitura. A verificacao de consistencia
sequencia/mutacao usa as amostras estratificadas derivadas, nao os brutos, por custo.

Uso:
    python -I exploratoria/src/eda_dominio.py \
        --data-dir data/external/zenodo-17620759 \
        --amostras exploratoria/resultados/amostras \
        --out-dir exploratoria/resultados
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

TOKEN = re.compile(r"^([A-Z])(\d+)([A-Z*])$")


def carrega(csv: Path) -> pd.DataFrame:
    df = pd.read_csv(csv, usecols=["mutant", "DMS_score", "DMS_score_bin"])
    df = df.dropna(subset=["mutant", "DMS_score"])
    df["mutant"] = df["mutant"].astype(str)
    df["tokens"] = df["mutant"].str.split(":")
    df["ordem"] = df["tokens"].str.len()
    return df


def por_coluna(df: pd.DataFrame, nome: str) -> list[dict]:
    """Estatisticas EXATAS por coluna, sobre os dados completos."""
    out = []
    y = df["DMS_score"].to_numpy(float)
    out.append({
        "conjunto": nome, "coluna": "DMS_score", "tipo": "numerica",
        "n": len(y), "ausentes": 0,
        "min": round(float(y.min()), 4), "max": round(float(y.max()), 4),
        "media": round(float(y.mean()), 4), "mediana": round(float(np.median(y)), 4),
        "dp": round(float(y.std(ddof=1)), 4),
        "q1": round(float(np.quantile(y, 0.25)), 4),
        "q3": round(float(np.quantile(y, 0.75)), 4),
        "iqr": round(float(np.quantile(y, 0.75) - np.quantile(y, 0.25)), 4),
        "mad": round(float(np.median(np.abs(y - np.median(y)))), 4),
        "distintos": int(pd.Series(y).nunique()),
    })
    b = df["DMS_score_bin"]
    out.append({
        "conjunto": nome, "coluna": "DMS_score_bin", "tipo": "binaria",
        "n": int(b.notna().sum()), "ausentes": int(b.isna().sum()),
        "distintos": int(b.nunique()),
        "fracao_1": round(float((b == 1).mean()), 4),
    })
    out.append({
        "conjunto": nome, "coluna": "mutant", "tipo": "texto",
        "n": len(df), "ausentes": 0,
        "distintos": int(df["mutant"].nunique()),
        "duplicados": int(len(df) - df["mutant"].nunique()),
        "ordem_min": int(df["ordem"].min()), "ordem_max": int(df["ordem"].max()),
    })
    return out


def por_ordem(df: pd.DataFrame, nome: str) -> list[dict]:
    y = df["DMS_score"].to_numpy(float)
    piso, teto = float(y.min()), float(y.max())
    out = []
    for k, g in df.groupby("ordem"):
        yk = g["DMS_score"].to_numpy(float)
        out.append({
            "conjunto": nome, "ordem": int(k), "n": len(yk),
            "media": round(float(yk.mean()), 4),
            "mediana": round(float(np.median(yk)), 4),
            "iqr": round(float(np.quantile(yk, .75) - np.quantile(yk, .25)), 4),
            "mad": round(float(np.median(np.abs(yk - np.median(yk)))), 4),
            "dp": round(float(yk.std(ddof=1)), 4) if len(yk) > 1 else None,
            "frac_no_piso": round(float(np.isclose(yk, piso).mean()), 4),
            "frac_no_teto": round(float(np.isclose(yk, teto).mean()), 4),
        })
    return out


def correlacoes(df: pd.DataFrame, nome: str) -> dict:
    y = df["DMS_score"].to_numpy(float)
    ordem = df["ordem"].to_numpy(float)
    r_ordem = float(spearmanr(ordem, y).statistic) if df["ordem"].nunique() > 1 else np.nan

    # consistencia bin x score: o bin e um corte no score?
    b = df["DMS_score_bin"]
    coer = np.nan
    limiar = np.nan
    if b.notna().all() and b.nunique() == 2:
        s1, s0 = y[b == 1], y[b == 0]
        if len(s1) and len(s0):
            limiar = float((s1.min() + s0.max()) / 2)
            coer = round(float(((y >= limiar) == (b == 1)).mean()), 4)
    return {"conjunto": nome,
            "spearman_score_vs_ordem": round(r_ordem, 4) if r_ordem == r_ordem else None,
            "limiar_implicito_do_bin": round(limiar, 4) if limiar == limiar else None,
            "coerencia_bin_limiar": coer if coer == coer else None}


def epistasia(df: pd.DataFrame, nome: str) -> dict:
    """Viabilidade da pergunta de negocio: quantos candidatos existem."""
    singles = df[df["ordem"] == 1]
    mapa = dict(zip(singles["mutant"], singles["DMS_score"], strict=True))
    if not mapa:
        return {"conjunto": nome, "erro": "sem singles medidos"}
    med_s = float(np.median(list(mapa.values())))
    p90 = float(np.quantile(df["DMS_score"], 0.90))

    multi = df[df["ordem"] >= 2]
    n_multi = len(multi)
    completos = supera = compens = 0
    for toks, score in zip(multi["tokens"], multi["DMS_score"], strict=True):
        vals = [mapa.get(t) for t in toks]
        if any(v is None for v in vals):
            continue
        completos += 1
        if score > max(vals):
            supera += 1
        if all(v <= med_s for v in vals) and score >= p90:
            compens += 1
    return {
        "conjunto": nome,
        "n_singles_medidos": len(mapa),
        "n_multimutantes": n_multi,
        "n_com_todos_singles": completos,
        "frac_sem_todos_singles": round(1 - completos / n_multi, 4) if n_multi else None,
        "n_supera_as_partes": supera,
        "frac_supera_as_partes": round(supera / completos, 4) if completos else None,
        "n_compensatorio": compens,
        "frac_compensatorio": round(compens / completos, 4) if completos else None,
        "mediana_dos_singles": round(med_s, 4),
        "p90_do_conjunto": round(p90, 4),
    }


def consistencia_sequencia(amostra: Path, nome: str) -> dict:
    """A mutacao declarada bate com a sequencia? Usa a amostra derivada."""
    df = pd.read_csv(amostra, usecols=["mutant", "mutated_sequence"]).dropna()
    comp = df["mutated_sequence"].astype(str).str.len()
    n_ver = bate = mal_formado = fora = 0
    for mut, seq in zip(df["mutant"].astype(str), df["mutated_sequence"].astype(str),
                        strict=True):
        for t in mut.split(":"):
            m = TOKEN.match(t)
            if not m:
                mal_formado += 1
                continue
            _, pos, novo = m.group(1), int(m.group(2)), m.group(3)
            if not 1 <= pos <= len(seq):
                fora += 1
                continue
            n_ver += 1
            bate += seq[pos - 1] == novo
    return {
        "conjunto": nome, "n_linhas_amostra": len(df),
        "comprimento_unico": bool(comp.nunique() == 1),
        "comprimento": int(comp.iloc[0]) if comp.nunique() == 1 else None,
        "tokens_verificados": n_ver,
        "frac_mutacao_bate_sequencia": round(bate / n_ver, 4) if n_ver else None,
        "tokens_mal_formados": mal_formado,
        "tokens_posicao_fora_da_sequencia": fora,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--amostras", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cols, ordens, cors, epis, seqs = [], [], [], [], []
    for csv in sorted(Path(args.data_dir).glob("*.csv")):
        nome = csv.name.removesuffix(".csv")
        df = carrega(csv)
        cols += por_coluna(df, nome)
        ordens += por_ordem(df, nome)
        cors.append(correlacoes(df, nome))
        epis.append(epistasia(df, nome))
        am = Path(args.amostras) / csv.name
        if am.exists():
            seqs.append(consistencia_sequencia(am, nome))
        print(f"  {nome:<38} n={len(df):>7} ordens={df['ordem'].nunique():>2}",
              flush=True)

    for nm, dados in (("colunas", cols), ("por_ordem", ordens),
                      ("correlacoes", cors), ("epistasia", epis),
                      ("consistencia_sequencia", seqs)):
        pd.DataFrame(dados).to_csv(out / f"eda_{nm}.tsv", sep="\t", index=False)
        print(f"  -> eda_{nm}.tsv ({len(dados)} linhas)")


if __name__ == "__main__":
    main()
