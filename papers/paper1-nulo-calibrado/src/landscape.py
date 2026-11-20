"""Carregamento de paisagens DMS e construcao da matriz de desenho binaria.

Esquema dos CSVs (ProteinGym, conforme distribuidos em Zenodo 10.5281/zenodo.17620759):

    mutant,mutated_sequence,DMS_score,DMS_score_bin

onde `mutant` e uma lista de tokens separados por ':' (ex. 'L59M:W60T:K64W') e a
ordem mutacional e o numero de tokens. A representacao usada em todo o projeto e a
do modelo aditivo: x_i em {0,1}^p indicando quais das p mutacoes pontuais distintas
estao presentes na variante i.

Os dados sao de terceiros e tratados como entrada: caminhos chegam por argumento.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

# Mapeamento entre os nomes de arquivo do Zenodo e os nomes usados nas tabelas
# suplementares de Tran et al. (Tabelas S3, S4, S7).
DATASET_NAMES: dict[str, str] = {
    "CAPSD_AAV2S_Sinai_2021": "AAV2 VP1",
    "SPG1_STRSG_Wu_2016": "GB1",
    "HIS7_YEAST_Pokusaeva_2019": "IGP dehydratase",
    "Q65J43_BACLD_g4_Thomas_2025": "NucB",
    "F7YBW8_MESOW_Aakre_2015": "ParD3",
    "PHOT_CHLRE_Chen_2023": "Phototropin",
    "TRPB1_THEMA_Tm9D8_Johnston_2024": "TrpB",
    "Q8WTC7_9CNID_Somermeyer_2022": "amacGFP",
    "GFP_AEQVI_Sarkisyan_2016": "avGFP",
    "D7PM05_CLYGR_Somermeyer_2022": "cgreGFP",
    "Q6WV13_9MAXI_Somermeyer_2022": "ppluGFP2",
    "VH14_Li_2023": "scFv",
}


@dataclass
class Landscape:
    """Paisagem genotipo-fenotipo em representacao aditiva."""

    name: str
    X: sp.csr_matrix          # (n, p) binaria: presenca de cada mutacao pontual
    y: np.ndarray             # (n,) fenotipo na escala declarada
    order: np.ndarray         # (n,) ordem mutacional
    mutations: list[str]      # (p,) rotulos das colunas de X
    scale: str                # transformacao aplicada a y

    @property
    def n(self) -> int:
        return self.X.shape[0]

    @property
    def p(self) -> int:
        return self.X.shape[1]

    def subset(self, mask: np.ndarray) -> Landscape:
        return Landscape(
            name=self.name,
            X=self.X[mask],
            y=self.y[mask],
            order=self.order[mask],
            mutations=self.mutations,
            scale=self.scale,
        )

    def order_counts(self) -> dict[int, int]:
        vals, cnts = np.unique(self.order, return_counts=True)
        return {int(v): int(c) for v, c in zip(vals, cnts, strict=True)}

    def __repr__(self) -> str:
        return (
            f"Landscape({self.name!r}, n={self.n}, p={self.p}, "
            f"escala={self.scale!r}, ordens={sorted(self.order_counts())[:6]}...)"
        )


def load_landscape(csv_path: str | Path, scale: str = "identity") -> Landscape:
    """Le um CSV de DMS e devolve a paisagem em representacao aditiva.

    Parameters
    ----------
    csv_path:
        Caminho do CSV (esquema ProteinGym).
    scale:
        Transformacao de y. 'identity' mantem como esta; 'log' aplica log natural
        (exige y > 0 e e a escala em que aditividade e biofisicamente esperada);
        'log1p' aplica log(1+y). A escolha e deliberada e registrada na paisagem,
        porque comparar aditivo e FCNN em escalas diferentes nao e a mesma
        comparacao (ver ESPECIFICACAO.md, secao 'Passo 1 - Escala').
    """
    path = Path(csv_path)
    df = pd.read_csv(path, usecols=["mutant", "DMS_score"])
    df = df.dropna(subset=["mutant", "DMS_score"])
    df = df[df["mutant"].astype(str).str.len() > 0]

    tokens = df["mutant"].astype(str).str.split(":")

    # Vocabulario de mutacoes pontuais, em ordem estavel (alfabetica) para
    # reprodutibilidade entre execucoes.
    vocab = sorted({tok for toks in tokens for tok in toks})
    index = {m: j for j, m in enumerate(vocab)}

    rows, cols = [], []
    for i, toks in enumerate(tokens):
        for tok in toks:
            rows.append(i)
            cols.append(index[tok])
    n, p = len(df), len(vocab)
    X = sp.csr_matrix(
        (np.ones(len(rows), dtype=np.float64), (rows, cols)), shape=(n, p)
    )

    y = df["DMS_score"].to_numpy(dtype=np.float64)
    if scale == "identity":
        pass
    elif scale == "log":
        if np.any(y <= 0):
            raise ValueError(
                f"{path.name}: escala 'log' pedida mas ha {int((y <= 0).sum())} "
                "valores <= 0. Use 'log1p' ou justifique um deslocamento."
            )
        y = np.log(y)
    elif scale == "log1p":
        if np.any(y <= -1):
            raise ValueError(f"{path.name}: escala 'log1p' exige y > -1.")
        y = np.log1p(y)
    else:
        raise ValueError(f"escala desconhecida: {scale!r}")

    order = np.asarray(X.sum(axis=1)).ravel().astype(int)
    stem = path.name.removesuffix(".csv")

    return Landscape(
        name=DATASET_NAMES.get(stem, stem),
        X=X,
        y=y,
        order=order,
        mutations=vocab,
        scale=scale,
    )
