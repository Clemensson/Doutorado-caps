"""Gera amostras estratificadas por ordem mutacional, em arquivos DERIVADOS.

POR QUE ISTO EXISTE. As ferramentas da skill `exploratory-data-analysis` limitam a
leitura por numero de linhas, e a propria skill avisa que isso le o INICIO do arquivo,
nao uma amostra aleatoria. Medimos a ordenacao dos 12 CSVs e o vies e real:

    Q65J43 (NucB)      ordem media das 1000 primeiras linhas 1,78  contra 8,29 no total
    VH14   (scFv)                                            2,87  contra 5,11
    PHOT   (Phototropin)                                     6,00  contra 7,98
    SPG1   (GB1)                                             2,91  contra 3,80

O NucB esta ordenado crescentemente por ordem mutacional: ler o prefixo veria quase so
singles e duplos. Alem disso tres arquivos passam do limite padrao de 64 MiB da skill
(HIS7 130 MB, SPG1 70 MB, TRPB1 65 MB).

A skill sanciona explicitamente a alternativa: "if broader coverage is needed, inspect
a documented stratified sample in a separate derived file within the same resource
limits".

CONTRATO. Os CSVs brutos sao abertos somente para leitura e nunca modificados. As
amostras vao para exploratoria/resultados/amostras/ como artefatos derivados.

ESTRATIFICACAO. Proporcional por ordem mutacional, com piso: cada ordem presente no
conjunto contribui ao menos MIN_POR_ESTRATO linhas (ou todas, se tiver menos). Isso
garante que ordens raras — justamente as de ordem alta — aparecam na amostra, ao preco
de a amostra nao ser proporcional nas caudas. O peso de cada estrato e gravado no
manifesto para que qualquer estatistica possa ser reponderada.

Uso:
    python -I exploratoria/src/amostra_estratificada.py \
        --data-dir data/external/zenodo-17620759 \
        --out-dir exploratoria/resultados/amostras \
        --alvo 20000
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

SEMENTE = 20261126
MIN_POR_ESTRATO = 200


def amostrar(csv: Path, alvo: int, rng: np.random.Generator) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(csv)
    n_total = len(df)
    ordem = df["mutant"].astype(str).str.count(":") + 1
    df = df.assign(_ordem=ordem)

    tam = df["_ordem"].value_counts().sort_index()
    # alocacao proporcional com piso por estrato
    prop = (tam / n_total * alvo).round().astype(int)
    aloc = np.minimum(np.maximum(prop, MIN_POR_ESTRATO), tam)

    partes, estratos = [], []
    for k, n_k in aloc.items():
        sub = df[df["_ordem"] == k]
        tomado = sub.sample(n=int(n_k), random_state=int(rng.integers(0, 2**31)))
        partes.append(tomado)
        estratos.append({
            "ordem": int(k),
            "n_populacao": int(tam[k]),
            "n_amostra": int(n_k),
            "peso": round(float(tam[k]) / float(n_k), 4),
        })

    am = pd.concat(partes, ignore_index=True).drop(columns="_ordem")
    manifesto = {
        "arquivo_origem": csv.name,
        "n_populacao": int(n_total),
        "n_amostra": int(len(am)),
        "fracao": round(len(am) / n_total, 4),
        "semente": SEMENTE,
        "min_por_estrato": MIN_POR_ESTRATO,
        "estratos": estratos,
    }
    return am, manifesto


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--alvo", type=int, default=20000)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEMENTE)

    manifestos = []
    for csv in sorted(Path(args.data_dir).glob("*.csv")):
        am, man = amostrar(csv, args.alvo, rng)
        destino = out / csv.name
        am.to_csv(destino, index=False)
        man["sha256_amostra"] = hashlib.sha256(destino.read_bytes()).hexdigest()[:16]
        man["mb_amostra"] = round(destino.stat().st_size / 1048576, 1)
        manifestos.append(man)
        print(f"  {csv.name:<38} {man['n_populacao']:>7} -> "
              f"{man['n_amostra']:>6} linhas  {man['mb_amostra']:>5} MB  "
              f"{len(man['estratos'])} estratos", flush=True)

    (out / "manifesto.json").write_text(
        json.dumps({"gerado_em": date.today().isoformat(),
                    "semente": SEMENTE,
                    "conjuntos": manifestos}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(f"\nmanifesto: {out / 'manifesto.json'}")
    print(f"maior amostra: {max(m['mb_amostra'] for m in manifestos)} MB "
          f"(limite padrao da skill: 64 MiB)")


if __name__ == "__main__":
    main()
