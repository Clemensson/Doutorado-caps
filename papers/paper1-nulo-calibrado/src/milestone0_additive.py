"""Marco zero: a progressao da Fig. 2E aparece sem nenhuma capacidade epistatica?

Tran et al. treinaram FCNNs em subconjuntos encaixados (carga maxima de treino 1, 2
e 3) e observaram que o desempenho em multimutantes separados melhora conforme o
treino e enriquecido (Spearman-Test medio 0,2251 -> 0,5062 -> 0,5986, Tabela S3),
interpretando isso como aprendizado de epistasia.

Este script treina **apenas ridge aditivo** — um modelo que, por construcao, nao pode
representar interacao nenhuma — no mesmo desenho encaixado, e mede a mesma
progressao. Se o padrao aparecer, o artefato de reducao de variancia esta demonstrado
de forma independente no nosso proprio pipeline, e a necessidade do Nulo Aditivo
Calibrado fica estabelecida sem depender de nenhuma afirmacao sobre a FCNN.

Uso:
    python -I papers/paper1-nulo-calibrado/src/milestone0_additive.py \
        --data-dir data/external/zenodo-17620759 \
        --out papers/paper1-nulo-calibrado/results/milestone0.tsv \
        [--datasets ParD3 GB1 TrpB] [--test-min-order 4]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import RidgeCV

sys.path.insert(0, str(Path(__file__).resolve().parent))
from landscape import DATASET_NAMES, Landscape, load_landscape  # noqa: E402

ALPHAS = np.logspace(-3.0, 4.0, 29)
TRAIN_LOADS = (1, 2, 3)


def evaluate_nested(
    land: Landscape, test_min_order: int = 4, seed: int = 0
) -> list[dict]:
    """Treina ridge aditivo em ordens <= L e avalia no MESMO teste fixo.

    O conjunto de teste e fixo entre os valores de L — variantes de ordem
    >= test_min_order — para que a unica coisa que muda seja o enriquecimento do
    treino. Essa e a comparacao que isola o efeito de reducao de variancia.
    """
    test_mask = land.order >= test_min_order
    n_test = int(test_mask.sum())
    if n_test == 0:
        return []

    X_test = land.X[test_mask]
    y_test = land.y[test_mask]
    order_test = land.order[test_mask]

    rows: list[dict] = []
    for load in TRAIN_LOADS:
        train_mask = (land.order >= 1) & (land.order <= load) & ~test_mask
        n_train = int(train_mask.sum())
        if n_train < 10:
            rows.append(
                {
                    "dataset": land.name,
                    "escala": land.scale,
                    "carga_treino": load,
                    "n_treino": n_train,
                    "n_teste": n_test,
                    "spearman": np.nan,
                    "pearson": np.nan,
                    "alpha": np.nan,
                    "p_colunas_vistas": 0,
                    "frac_teste_com_mut_nao_vista": np.nan,
                    "segundos": 0.0,
                    "nota": "treino insuficiente",
                }
            )
            continue

        X_train = land.X[train_mask]
        y_train = land.y[train_mask]

        # Mutacoes nunca observadas no treino tem coeficiente nao identificado.
        # Decisao declarada (ESPECIFICACAO.md, 3.4): encolher a zero, mantendo a
        # coluna. Contabilizamos o quanto do teste isso afeta.
        seen = np.asarray(X_train.sum(axis=0)).ravel() > 0
        n_seen = int(seen.sum())
        unseen_contrib = X_test[:, ~seen].sum(axis=1)
        frac_unseen = float((np.asarray(unseen_contrib).ravel() > 0).mean())

        t0 = time.perf_counter()
        model = RidgeCV(alphas=ALPHAS, fit_intercept=True, cv=5)
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        elapsed = time.perf_counter() - t0

        rho = spearmanr(pred, y_test).statistic
        r = float(np.corrcoef(pred, y_test)[0, 1])

        rows.append(
            {
                "dataset": land.name,
                "escala": land.scale,
                "carga_treino": load,
                "n_treino": n_train,
                "n_teste": n_test,
                "spearman": float(rho),
                "pearson": r,
                "alpha": float(model.alpha_),
                "p_colunas_vistas": n_seen,
                "frac_teste_com_mut_nao_vista": frac_unseen,
                "segundos": round(elapsed, 2),
                "nota": "",
            }
        )

        # Spearman estratificado por ordem exata do teste, para o mapa de regimes.
        for k in np.unique(order_test):
            km = order_test == k
            if km.sum() < 20:
                continue
            rows.append(
                {
                    "dataset": land.name,
                    "escala": land.scale,
                    "carga_treino": load,
                    "n_treino": n_train,
                    "n_teste": int(km.sum()),
                    "spearman": float(spearmanr(pred[km], y_test[km]).statistic),
                    "pearson": float(np.corrcoef(pred[km], y_test[km])[0, 1]),
                    "alpha": float(model.alpha_),
                    "p_colunas_vistas": n_seen,
                    "frac_teste_com_mut_nao_vista": frac_unseen,
                    "segundos": 0.0,
                    "nota": f"ordem_teste={int(k)}",
                }
            )

    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--datasets", nargs="*", default=None,
                    help="nomes como em Tran et al. (ParD3, GB1, TrpB...). Padrao: todos.")
    ap.add_argument("--test-min-order", type=int, default=4)
    ap.add_argument("--scale", default="identity", choices=["identity", "log", "log1p"])
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    stem_by_name = {v: k for k, v in DATASET_NAMES.items()}

    if args.datasets:
        stems = []
        for nm in args.datasets:
            if nm in stem_by_name:
                stems.append(stem_by_name[nm])
            elif nm in DATASET_NAMES:
                stems.append(nm)
            else:
                sys.exit(f"conjunto desconhecido: {nm!r}")
    else:
        stems = sorted(DATASET_NAMES)

    all_rows: list[dict] = []
    for stem in stems:
        csv = data_dir / f"{stem}.csv"
        if not csv.exists():
            print(f"  !! ausente: {csv.name}", flush=True)
            continue
        land = load_landscape(csv, scale=args.scale)
        print(f"[{land.name}] n={land.n} p={land.p} escala={land.scale}", flush=True)
        rows = evaluate_nested(land, test_min_order=args.test_min_order)
        if not rows:
            print(f"  !! sem variantes de ordem >= {args.test_min_order}", flush=True)
            continue
        all_rows.extend(rows)
        for rr in rows:
            if not rr["nota"]:
                print(
                    f"   carga {rr['carga_treino']}: n_treino={rr['n_treino']:>7} "
                    f"spearman={rr['spearman']:.4f} alpha={rr['alpha']:.3g} "
                    f"({rr['segundos']}s)",
                    flush=True,
                )

    df = pd.DataFrame(all_rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, sep="\t", index=False)
    print(f"\nescrito: {out}  ({len(df)} linhas)")

    agg = df[df["nota"] == ""].pivot_table(
        index="dataset", columns="carga_treino", values="spearman"
    )
    print("\n== Spearman no teste (ridge ADITIVO), por carga de treino ==")
    print(agg.round(4).to_string())
    if not agg.empty:
        print("\nmedia por carga:")
        print(agg.mean(axis=0).round(4).to_string())


if __name__ == "__main__":
    main()
