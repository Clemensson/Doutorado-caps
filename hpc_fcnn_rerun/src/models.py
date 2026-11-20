"""A FCNN do MULTI-evolve, reimplementada fielmente, e o baseline ridge aditivo.

A arquitetura e o regime de treino vem de
`multievolve/predictors/neural_net_regressors.py` (classes `Fcn` e `BaseNN`):

    nn_arch = [layer_size] * num_layers
    layers  = [Linear(input, nn_arch[0]), LeakyReLU(0.2), Dropout(0.2)]
    for i in range(len(nn_arch)):
        if i <  len(nn_arch)-1: layers += [Linear(nn_arch[i], nn_arch[i+1]),
                                           LeakyReLU(0.2), Dropout(0.2)]
        if i == len(nn_arch)-1: layers += [Linear(nn_arch[i], 1)]

    criterion = MSELoss();  optimizer = Adam(lr);  epochs = 300
    early stopping: patience = 15, delta minimo = 1e-5, sobre a perda de validacao

DESVIO DECLARADO: o `val_split` do codigo original e `None` por padrao e o valor
usado no benchmarking da Fig. 2E nao esta documentado em nenhuma das fontes
disponiveis (codigo, suplementar, notebook de reanalise). Aqui usamos uma fracao
configuravel do subconjunto de treino (padrao 0,10), amostrada de forma
estratificada por carga mutacional. Isso e necessario porque o early stopping exige
validacao. A sensibilidade a essa escolha deve ser reportada.
"""

from __future__ import annotations

import time

import numpy as np
import torch
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import RidgeCV
from torch import nn

RIDGE_ALPHAS = np.logspace(-3, 3, 50)
EPOCHS = 300
PATIENCE = 15
VAL_LOSS_DELTA_MIN = 1e-5


def build_fcnn(input_dim: int, layer_size: int, num_layers: int) -> nn.Sequential:
    if num_layers < 1:
        raise ValueError("num_layers deve ser >= 1 (nn_arch[0] exige ao menos uma)")
    arch = [layer_size] * num_layers
    layers: list[nn.Module] = [
        nn.Linear(input_dim, arch[0]),
        nn.LeakyReLU(negative_slope=0.2),
        nn.Dropout(p=0.2),
    ]
    for i in range(len(arch)):
        if i < len(arch) - 1:
            layers += [
                nn.Linear(arch[i], arch[i + 1]),
                nn.LeakyReLU(negative_slope=0.2),
                nn.Dropout(p=0.2),
            ]
        if i == len(arch) - 1:
            layers += [nn.Linear(arch[i], 1)]
    return nn.Sequential(*layers)


def stratified_val_split(
    loads: np.ndarray, val_frac: float, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Separa validacao estratificando por carga mutacional."""
    rng = np.random.RandomState(seed)
    tr_parts, va_parts = [], []
    for k in np.unique(loads):
        idx = np.where(loads == k)[0]
        rng.shuffle(idx)
        n_val = max(1, int(round(len(idx) * val_frac))) if len(idx) >= 5 else 0
        va_parts.append(idx[:n_val])
        tr_parts.append(idx[n_val:])
    return np.concatenate(tr_parts), np.concatenate(va_parts)


def _predict_batched(
    model: nn.Module, ds, idx: np.ndarray, featurization: str,
    device: torch.device, batch: int = 2048,
) -> np.ndarray:
    model.eval()
    out = np.empty(len(idx), dtype=np.float64)
    with torch.no_grad():
        for s in range(0, len(idx), batch):
            chunk = idx[s : s + batch]
            Xb = torch.from_numpy(ds.featurize(chunk, featurization)).to(device)
            out[s : s + len(chunk)] = model(Xb).squeeze(-1).cpu().numpy()
    return out


def fit_fcnn(
    ds,
    train_idx: np.ndarray,
    featurization: str,
    layer_size: int,
    num_layers: int,
    learning_rate: float,
    batch_size: int,
    device: torch.device,
    seed: int,
    val_frac: float = 0.10,
    epochs: int = EPOCHS,
) -> tuple[nn.Module, int, float]:
    """Treina a FCNN. Devolve (modelo, epocas efetivas, segundos)."""
    torch.manual_seed(seed)
    t0 = time.perf_counter()

    sub_tr, sub_va = stratified_val_split(ds.n_muts[train_idx], val_frac, seed)
    tr_idx = train_idx[sub_tr]
    va_idx = train_idx[sub_va] if len(sub_va) else train_idx[sub_tr][:0]

    model = build_fcnn(ds.input_dim(featurization), layer_size, num_layers).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()

    y_tr = torch.from_numpy(ds.y[tr_idx].astype(np.float32)).to(device)
    has_val = len(va_idx) >= 2
    if has_val:
        X_va = torch.from_numpy(ds.featurize(va_idx, featurization)).to(device)
        y_va = torch.from_numpy(ds.y[va_idx].astype(np.float32)).to(device)

    best_val = float("inf")
    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    no_improve = 0
    rng = np.random.RandomState(seed)
    n_tr = len(tr_idx)
    epochs_run = 0

    for epoch in range(epochs):
        epochs_run = epoch + 1
        model.train()
        perm = rng.permutation(n_tr)
        for s in range(0, n_tr, batch_size):
            sel = perm[s : s + batch_size]
            Xb = torch.from_numpy(ds.featurize(tr_idx[sel], featurization)).to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(Xb).squeeze(-1), y_tr[sel])
            loss.backward()
            optimizer.step()

        if not has_val:
            continue
        model.eval()
        with torch.no_grad():
            val_loss = float(criterion(model(X_va).squeeze(-1), y_va).item())
        if val_loss < best_val - VAL_LOSS_DELTA_MIN:
            best_val = val_loss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= PATIENCE:
                break

    if has_val:
        model.load_state_dict(best_state)
    return model, epochs_run, time.perf_counter() - t0


def fit_additive(ds, train_idx: np.ndarray) -> tuple[RidgeCV, float, float]:
    """Ridge aditivo sobre o indicador de mutacao. Devolve (modelo, alpha, segundos)."""
    t0 = time.perf_counter()
    X_tr = np.asarray(ds.X_mut[train_idx].todense(), dtype=np.float64)
    model = RidgeCV(alphas=RIDGE_ALPHAS, fit_intercept=True)
    model.fit(X_tr, ds.y[train_idx])
    return model, float(model.alpha_), time.perf_counter() - t0


def corr(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    if np.std(p) <= 0 or np.std(y) <= 0:
        return 0.0, 0.0
    return float(pearsonr(y, p).statistic), float(spearmanr(y, p).statistic)


def predict_fcnn(model, ds, idx, featurization, device):
    return _predict_batched(model, ds, idx, featurization, device)
