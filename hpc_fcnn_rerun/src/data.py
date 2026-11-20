"""Dados e particoes do protocolo de benchmarking de Tran et al. (Fig. 2E/F).

Modulo autocontido: nao importa nada do projeto pai, para que este diretorio possa
ser copiado isoladamente para o HPC.

Protocolo replicado (ver PROTOCOLO_ALINHADO.md no projeto):
  1. Filtro de estringencia 'singles': mantem apenas variantes cujas mutacoes
     constituintes TODAS existam como single mutante medido.
  2. Normalizacao min-max de DMS_score para [0, 1].
  3. Particao: pool de CV = cargas 1-3;  teste extra = cargas >= 4.
  4. Pool de CV em 5 folds (semente 42).
  5. Treino = variantes de carga <= L dos outros 4 folds.
  6. Avaliacao em cargas >= 3: global e por carga exata.

Duas featurizacoes:
  - 'seq': one-hot da sequencia inteira, 22 categorias por posicao
    (20 aminoacidos + '*' + 'X'), replicando OneHotFeaturizer do MULTI-evolve.
    E o que a FCNN publicada recebeu.
  - 'mut': indicador binario de mutacao, p = numero de mutacoes pontuais
    distintas. E o que o baseline aditivo usa.

As duas geram a MESMA classe de funcoes: o one-hot de sequencia e uma transformacao
afim do indicador de mutacao, ja que nenhuma variante tem duas substituicoes na
mesma posicao, e a primeira camada linear absorve a transformacao. O que difere e a
geometria de otimizacao, a dimensao de entrada e como o dropout age.

A ordem das categorias de aminoacido e irrelevante para um MLP (permutacao das
features de entrada), portanto nao e preciso reproduzi-la exatamente.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

AA_CATEGORIES = [
    "A", "C", "D", "E", "F", "G", "H", "I", "K", "L",
    "M", "N", "P", "Q", "R", "S", "T", "V", "W", "Y",
    "*", "X",
]
N_CATEGORIES = len(AA_CATEGORIES)  # 22
AA_TO_CODE = {aa: i for i, aa in enumerate(AA_CATEGORIES)}

CV_POOL_MAX_LOAD = 3
EXTRA_TEST_MIN_LOAD = 4
TRAIN_LOADS = (1, 2, 3)
N_FOLDS = 5
FOLD_SEED = 42


@dataclass
class Dataset:
    name: str
    y: np.ndarray                 # (n,) min-max para [0,1]
    n_muts: np.ndarray            # (n,) carga mutacional
    X_mut: sp.csr_matrix          # (n, p) indicador de mutacao
    seq_codes: np.ndarray | None  # (n, L) int8 — codigo de aminoacido por posicao
    mutations: list[str]
    seq_len: int

    @property
    def n(self) -> int:
        return len(self.y)

    def input_dim(self, featurization: str) -> int:
        if featurization == "mut":
            return self.X_mut.shape[1]
        if featurization == "seq":
            return self.seq_len * N_CATEGORIES
        raise ValueError(featurization)

    def featurize(self, idx: np.ndarray, featurization: str) -> np.ndarray:
        """Materializa as features de um subconjunto, em float32.

        O one-hot de sequencia NUNCA e materializado por inteiro: para GB1 seriam
        149k x 448 x 22 valores. Guardamos codigos inteiros (n x L, int8) e
        expandimos por lote aqui.
        """
        if featurization == "mut":
            return np.asarray(self.X_mut[idx].todense(), dtype=np.float32)
        if featurization == "seq":
            codes = self.seq_codes[idx]                      # (b, L)
            b, L = codes.shape
            out = np.zeros((b, L, N_CATEGORIES), dtype=np.float32)
            rows = np.repeat(np.arange(b), L)
            cols = np.tile(np.arange(L), b)
            out[rows, cols, codes.ravel()] = 1.0
            return out.reshape(b, L * N_CATEGORIES)
        raise ValueError(featurization)


def load_dataset(csv_path: str | Path, name: str, need_seq: bool = True) -> Dataset:
    path = Path(csv_path)
    usecols = ["mutant", "DMS_score"] + (["mutated_sequence"] if need_seq else [])
    df = pd.read_csv(path, usecols=usecols)
    df = df.dropna(subset=["mutant", "DMS_score"]).copy()
    df["mutant"] = df["mutant"].astype(str)

    tokens = df["mutant"].str.split(":")
    n_muts = tokens.str.len().to_numpy()

    # --- filtro de estringencia 'singles' ---
    singles = set(df.loc[n_muts == 1, "mutant"].tolist())
    keep = tokens.apply(lambda toks: all(t in singles for t in toks)).to_numpy()
    df = df[keep]
    tokens = tokens[keep]
    n_muts = n_muts[keep]

    # Ordenacao decrescente por carga, como preprocess_dataset faz (estavel aqui).
    order = np.argsort(-n_muts, kind="stable")
    df = df.iloc[order].reset_index(drop=True)
    tokens = tokens.iloc[order].reset_index(drop=True)
    n_muts = n_muts[order]

    # --- y: min-max para [0,1] ---
    y = df["DMS_score"].to_numpy(dtype=np.float64)
    ymin, ymax = float(y.min()), float(y.max())
    if ymax > ymin:
        y = (y - ymin) / (ymax - ymin)

    # --- indicador de mutacao ---
    vocab = sorted({t for toks in tokens for t in toks})
    index = {m: j for j, m in enumerate(vocab)}
    rows, cols = [], []
    for i, toks in enumerate(tokens):
        for t in toks:
            rows.append(i)
            cols.append(index[t])
    X_mut = sp.csr_matrix(
        (np.ones(len(rows), dtype=np.float32), (rows, cols)),
        shape=(len(df), len(vocab)),
    )

    # --- codigos de sequencia ---
    seq_codes = None
    seq_len = 0
    if need_seq:
        seqs = df["mutated_sequence"].astype(str).to_numpy()
        lengths = {len(s) for s in seqs}
        if len(lengths) != 1:
            raise ValueError(
                f"{name}: sequencias de comprimentos diferentes {sorted(lengths)[:5]} — "
                "o one-hot de sequencia pressupoe apenas substituicoes"
            )
        seq_len = lengths.pop()
        unknown = AA_TO_CODE["X"]
        seq_codes = np.empty((len(seqs), seq_len), dtype=np.int8)
        for i, s in enumerate(seqs):
            seq_codes[i] = [AA_TO_CODE.get(c, unknown) for c in s]

    return Dataset(
        name=name,
        y=y,
        n_muts=n_muts,
        X_mut=X_mut,
        seq_codes=seq_codes,
        mutations=vocab,
        seq_len=seq_len,
    )


def make_partition(ds: Dataset, n_folds: int = N_FOLDS, seed: int = FOLD_SEED):
    """Devolve (folds, cv_pool_idx, extra_test_idx)."""
    cv_pool_idx = np.where((ds.n_muts >= 1) & (ds.n_muts <= CV_POOL_MAX_LOAD))[0]
    extra_test_idx = np.where(ds.n_muts >= EXTRA_TEST_MIN_LOAD)[0]
    if len(cv_pool_idx) < n_folds:
        raise ValueError(f"{ds.name}: pool de CV muito pequeno ({len(cv_pool_idx)})")
    rng = np.random.RandomState(seed)
    shuffled = cv_pool_idx.copy()
    rng.shuffle(shuffled)
    folds = np.array_split(shuffled, n_folds)
    return folds, cv_pool_idx, extra_test_idx


def assemble_eval(
    ds: Dataset,
    y_pred_cv: np.ndarray,
    extra_mean: np.ndarray,
    cv_pool_idx: np.ndarray,
    extra_test_idx: np.ndarray,
):
    """Conjunto de avaliacao: pool de CV com carga >= 3 + todo o teste extra."""
    sel = cv_pool_idx[
        (ds.n_muts[cv_pool_idx] >= 3) & ~np.isnan(y_pred_cv[cv_pool_idx])
    ]
    y_true = np.concatenate([ds.y[sel], ds.y[extra_test_idx]])
    y_pred = np.concatenate([y_pred_cv[sel], extra_mean])
    loads = np.concatenate([ds.n_muts[sel], ds.n_muts[extra_test_idx]])
    return y_true, y_pred, loads
