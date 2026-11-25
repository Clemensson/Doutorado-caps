"""A FCNN DENTRO do Nulo Aditivo Calibrado.

POR QUE ISTO EXISTE. O NAC de `calibrated_null.py` calibra o ridge pareado, o modelo
de epistasia global e o aditivo — todos sklearn, nenhum deles a rede. Isso deixa duas
lacunas:

  (a) A OBJECAO DE REVISOR. A conclusao "epistasia especifica e pequena" repousa num
      ridge pareado. Um revisor pergunta, com razao: a FCNN, calibrada contra o mesmo
      nulo, encontra mais interacao que o pareado? Nao respondemos.

  (b) O NUMERO CENTRAL DO CAPITULO NAO ESTA CALIBRADO. A vantagem da FCNN sobre o
      aditivo em Pearson na interpolacao, +0,13, e a quantidade mais citada do
      capitulo — e nunca foi comparada contra o nulo. Calibramos o pareado e o
      global, nao a rede.

Este modulo roda, por celula (conjunto x carga de treino): aditivo, epistasia global,
FCNN e — onde o modelo e identificavel — ridge pareado. Todos nos MESMOS folds e nas
MESMAS paisagens simuladas, de modo que os efeitos calibrados sao diretamente
comparaveis entre si.

Cobertura: 12 conjuntos x 3 cargas = 36 celulas. O pareado so entra nos 5 conjuntos
com p + p(p-1)/2 <= 25.000 (ver config/nac_datasets.tsv); a FCNN nao tem essa
restricao, por isso a cobertura aqui e maior que a de `calibrated_null.py`.

FEATURIZACAO: 'mut' (indicador de mutacao). Deliberado — e a representacao que o
aditivo, o pareado e o global tambem usam, portanto a comparacao fica na mesma base.
O one-hot de sequencia foi medido fora do nulo (RESULTADOS_FCNN.md) e e mais caro.

B = 30 REPLICAS, nao 100. Custo medido no experimento 1: com B=30 a pior celula
(GB1 carga 3) leva 4,6 h e a soma das 36 da 23 h; com B=100 seriam 15,4 h e 77 h. O
piso do p calibrado sobe de 0,0099 para 1/31 = 0,0323, o que e suficiente porque os
efeitos em jogo (+0,13) sao ordens de magnitude maiores que a dispersao dos nulos
observada ate agora.

════════════════════════════════════════════════════════════════════════════════
CONCESSAO METODOLOGICA QUE PRECISA SER DECLARADA NO ARTIGO
════════════════════════════════════════════════════════════════════════════════

A armadilha 3.2 da ESPECIFICACAO exige que a selecao de hiperparametros aconteca
DENTRO do laco, pela mesma rotina usada nos dados reais. Para a FCNN isso e
inviavel: a varredura de Tran et al. tem 72 configuracoes, e 72 x 30 replicas x 36
celulas e impossivel. Usamos os hiperparametros publicados na Tabela S3, FIXOS,
iguais no real e no simulado.

Direcao do vies, que importa: os hiperparametros foram ajustados para os dados reais,
que contem epistasia. Numa paisagem simulada puramente aditiva eles podem ser
subotimos, de modo que a FCNN do nulo rende MENOS do que renderia bem ajustada. O
nulo fica baixo demais, e portanto o efeito calibrado (observado menos nulo) fica
ALTO demais.

Isso superestima o incremento de interacao da FCNN — ou seja, trabalha CONTRA a
hipotese do capitulo, que e de que esse incremento e pequeno. Um incremento medido
pequeno sob este vies e, por isso, um resultado forte; um incremento grande seria
ambiguo entre interacao genuina e artefato de hiperparametro.

Uso:
    python src/calibrated_null_fcnn.py --data-dir data \\
        --dataset GB1 --train-load 3 --replicates 30 \\
        --out results_nac_fcnn/GB1_L3.tsv
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import pearsonr, spearmanr
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import RidgeCV

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from calibrated_null import (  # noqa: E402
    ALPHAS,
    build_pairwise,
    fit_null_generator,
    sigma_para_ordens_nao_vistas,
    simulate,
)
from data import assemble_eval, load_dataset, make_partition  # noqa: E402
from models import fit_fcnn, predict_fcnn  # noqa: E402

P_PAREADO_MAX = 25_000
FEAT = "mut"


def _corr(y, p):
    if np.std(p) <= 0 or np.std(y) <= 0:
        return 0.0, 0.0
    return float(pearsonr(y, p).statistic), float(spearmanr(y, p).statistic)


def _ridge(X, y):
    return RidgeCV(alphas=ALPHAS, fit_intercept=True).fit(X, y)


def run_pipeline(d, y, Xa, Xp, folds, cv_pool_idx, extra_test_idx, load,
                 hp, device, val_frac, seed):
    """Aditivo, global, FCNN e (se houver Xp) pareado, nos mesmos folds."""
    models = ["additive", "global_iso", "fcnn"] + (["pairwise"] if Xp is not None else [])
    n = len(y)
    pred = {m: (np.full(n, np.nan), np.zeros((len(folds), len(extra_test_idx))))
            for m in models}
    d_sim = dataclasses.replace(d, y=y)

    for f, held in enumerate(folds):
        pool = np.concatenate([folds[j] for j in range(len(folds)) if j != f])
        tr = pool[d.n_muts[pool] <= load]
        if len(tr) < 10:
            continue

        Xtr = np.asarray(Xa[tr].todense())
        ma = _ridge(Xtr, y[tr])
        pred["additive"][0][held] = ma.predict(Xa[held])
        pred["additive"][1][f] = ma.predict(Xa[extra_test_idx])

        iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
        iso.fit(ma.predict(Xtr), y[tr])
        pred["global_iso"][0][held] = iso.predict(ma.predict(Xa[held]))
        pred["global_iso"][1][f] = iso.predict(ma.predict(Xa[extra_test_idx]))

        if Xp is not None:
            mp = _ridge(np.asarray(Xp[tr].todense()), y[tr])
            pred["pairwise"][0][held] = mp.predict(Xp[held])
            pred["pairwise"][1][f] = mp.predict(Xp[extra_test_idx])

        model, _, _ = fit_fcnn(
            d_sim, tr, FEAT,
            layer_size=int(hp["layer_size"]), num_layers=int(hp["num_layers"]),
            learning_rate=float(hp["learning_rate"]),
            batch_size=int(hp["batch_size"]),
            device=device, seed=seed + f, val_frac=val_frac,
        )
        pred["fcnn"][0][held] = predict_fcnn(model, d_sim, held, FEAT, device)
        pred["fcnn"][1][f] = predict_fcnn(model, d_sim, extra_test_idx, FEAT, device)
        del model

    out = {}
    for mname, (cv, extra) in pred.items():
        yt, yp, loads = assemble_eval(d_sim, cv, extra.mean(axis=0),
                                      cv_pool_idx, extra_test_idx)
        interp = loads <= load
        for regime, mask in (("all", np.ones(len(yt), bool)),
                             ("interpolacao", interp), ("extrapolacao", ~interp)):
            if mask.sum() < 3:
                continue
            out[(mname, regime)] = _corr(yt[mask], yp[mask])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--dataset")
    ap.add_argument("--train-load", type=int)
    ap.add_argument("--array-index", type=int)
    ap.add_argument("--replicates", type=int, default=30)
    ap.add_argument("--sigma-unseen", default="maior_ordem",
                    choices=["maior_ordem", "maior_sigma", "ordem2"])
    ap.add_argument("--val-frac", type=float, default=0.10)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--out-dir", default="results_nac_fcnn")
    ap.add_argument("--out")
    ap.add_argument("--list-jobs", action="store_true")
    args = ap.parse_args()

    cfg = pd.read_csv(ROOT.parent / "config" / "datasets.tsv", sep="\t")
    nomes = list(cfg.sort_values("custo_relativo", ascending=False)["dataset"])
    jobs = [(n, L) for L in (3, 2, 1) for n in nomes]

    if args.list_jobs:
        for i, (n, L) in enumerate(jobs):
            print(f"{i}\t{n}\tcarga {L}")
        return

    if args.array_index is not None:
        if not 0 <= args.array_index < len(jobs):
            sys.exit(f"indice fora da faixa 0..{len(jobs) - 1}")
        dataset, load = jobs[args.array_index]
    else:
        if not args.dataset or not args.train_load:
            sys.exit("informe --dataset e --train-load, ou --array-index")
        dataset, load = args.dataset, args.train_load

    out = Path(args.out) if args.out else (
        Path(args.out_dir) / f"{dataset.replace(' ', '_')}_L{load}.tsv")

    threads = int(os.environ.get("SLURM_CPUS_PER_TASK", 0))
    if threads:
        torch.set_num_threads(threads)
    dev = args.device
    if dev == "auto":
        dev = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(dev)

    arq = dict(zip(cfg["dataset"], cfg["arquivo"], strict=True))
    hp_all = pd.read_csv(ROOT.parent / "config" / "hyperparams.tsv", sep="\t")
    hpr = hp_all[(hp_all["dataset"] == dataset) & (hp_all["train_load"] == load)]
    if hpr.empty:
        sys.exit(f"sem hiperparametros para {dataset} carga {load}")
    hp = hpr.iloc[0]

    print(json.dumps({"dataset": dataset, "carga": load, "device": dev,
                      "B": args.replicates, "featurizacao": FEAT,
                      "val_frac": args.val_frac,
                      "hiperparametros": {k: str(hp[k]) for k in
                                          ("layer_size", "num_layers",
                                           "learning_rate", "batch_size")}},
                     ensure_ascii=False), flush=True)

    d = load_dataset(Path(args.data_dir) / arq[dataset], dataset, need_seq=False)
    folds, cv_pool_idx, extra_test_idx = make_partition(d)
    Xa = d.X_mut.tocsr()
    p = Xa.shape[1]
    p_par = p + p * (p - 1) // 2
    Xp = build_pairwise(Xa) if p_par <= P_PAREADO_MAX else None
    print(f"  n={d.n} p={p} p_pareado={p_par} "
          f"{'(pareado incluido)' if Xp is not None else '(pareado INESTIMAVEL, omitido)'}",
          flush=True)

    t0 = time.perf_counter()
    obs = run_pipeline(d, d.y, Xa, Xp, folds, cv_pool_idx, extra_test_idx,
                       load, hp, device, args.val_frac, args.seed)
    print(f"  observado em {time.perf_counter() - t0:.0f}s", flush=True)
    for (m, r), (pr, sr) in sorted(obs.items()):
        print(f"    {m:<11} {r:<13} r={pr:.4f} rho={sr:.4f}", flush=True)

    gen, sigma, n_tr = fit_null_generator(Xa, d.y, folds, d.n_muts, load)
    fb = sigma_para_ordens_nao_vistas(sigma, args.sigma_unseen)
    print(f"  gerador: n_treino={n_tr} sigma={{{', '.join(f'{k}: {v:.4f}' for k, v in sorted(sigma.items()))}}}"
          f"  nao visto -> {fb:.4f}", flush=True)

    rng = np.random.default_rng(args.seed)
    nulos: dict[tuple, list] = {}
    for b in range(args.replicates):
        y_sim = simulate(gen, sigma, Xa, d.n_muts, rng, args.sigma_unseen)
        res = run_pipeline(d, y_sim, Xa, Xp, folds, cv_pool_idx, extra_test_idx,
                           load, hp, device, args.val_frac, args.seed)
        for k, v in res.items():
            nulos.setdefault(k, []).append(v)
        if (b + 1) % 5 == 0 or b == 0:
            print(f"  replica {b + 1}/{args.replicates} "
                  f"({time.perf_counter() - t0:.0f}s acumulados)", flush=True)

    rows = []
    for mname in ("global_iso", "fcnn", "pairwise"):
        for regime in ("all", "interpolacao", "extrapolacao"):
            km, ka = (mname, regime), ("additive", regime)
            if km not in obs or ka not in obs or km not in nulos:
                continue
            for mi, met in ((0, "pearson"), (1, "spearman")):
                t_obs = obs[km][mi] - obs[ka][mi]
                t_null = np.array([nulos[km][b][mi] - nulos[ka][b][mi]
                                   for b in range(len(nulos[km]))])
                B = len(t_null)
                rows.append({
                    "dataset": dataset, "carga_treino": load, "modelo": mname,
                    "featurizacao": FEAT, "regime": regime, "metrica": met,
                    "ganho_observado": round(float(t_obs), 4),
                    "ganho_nulo_mediana": round(float(np.median(t_null)), 4),
                    "ganho_nulo_p05": round(float(np.quantile(t_null, 0.05)), 4),
                    "ganho_nulo_p95": round(float(np.quantile(t_null, 0.95)), 4),
                    "efeito_calibrado": round(float(t_obs - np.median(t_null)), 4),
                    "p_calibrado": round((1 + int((t_null >= t_obs).sum())) / (B + 1), 4),
                    "B": B, "sigma_unseen": args.sigma_unseen,
                    "val_frac": args.val_frac,
                    "hp_num_layers": int(hp["num_layers"]),
                    "hp_batch_size": int(hp["batch_size"]),
                })

    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, sep="\t", index=False)
    print(f"\nescrito: {out} ({len(rows)} linhas) em "
          f"{(time.perf_counter() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
