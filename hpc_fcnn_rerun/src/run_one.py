"""Roda o protocolo para UM conjunto e UMA featurizacao. Projetado para array job.

A FCNN e o ridge aditivo rodam nos MESMOS folds, no mesmo processo, de modo que a
comparacao e pareada dentro de cada fold — o que a comparacao contra a Tabela S4 nao
permitia.

Uso:
    python src/run_one.py --dataset GB1 --featurization seq \
        --data-dir data --out results/GB1_seq.tsv

    python src/run_one.py --array-index $SLURM_ARRAY_TASK_ID \
        --data-dir data --out-dir results
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import TRAIN_LOADS, assemble_eval, load_dataset, make_partition  # noqa: E402
from models import corr, fit_additive, fit_fcnn, predict_fcnn  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FEATURIZATIONS = ("seq", "mut")


def load_config():
    ds = pd.read_csv(ROOT / "config" / "datasets.tsv", sep="\t")
    hp = pd.read_csv(ROOT / "config" / "hyperparams.tsv", sep="\t")
    return ds, hp


def array_jobs() -> list[tuple[str, str]]:
    """Lista estavel de tarefas: (conjunto, featurizacao), ordenada por custo."""
    ds, _ = load_config()
    jobs = []
    for _, r in ds.sort_values("custo_relativo", ascending=False).iterrows():
        for f in FEATURIZATIONS:
            jobs.append((r["dataset"], f))
    return jobs


def run(dataset: str, featurization: str, data_dir: Path, out: Path,
        device_str: str, val_frac: float, epochs: int, seed: int) -> None:
    ds_cfg, hp = load_config()
    row = ds_cfg[ds_cfg["dataset"] == dataset]
    if row.empty:
        sys.exit(f"conjunto desconhecido: {dataset!r}")
    csv = data_dir / row.iloc[0]["arquivo"]
    if not csv.exists():
        sys.exit(f"arquivo de dados ausente: {csv}")

    device = torch.device(device_str)
    print(f"[{dataset}/{featurization}] device={device} carregando {csv.name}",
          flush=True)

    need_seq = featurization == "seq"
    d = load_dataset(csv, dataset, need_seq=need_seq)
    folds, cv_pool_idx, extra_test_idx = make_partition(d)
    print(f"  n={d.n}  p_mut={d.X_mut.shape[1]}  L={d.seq_len}  "
          f"entrada={d.input_dim(featurization)}  "
          f"pool_cv={len(cv_pool_idx)}  teste_extra={len(extra_test_idx)}",
          flush=True)

    rows: list[dict] = []
    for load in TRAIN_LOADS:
        hprow = hp[(hp["dataset"] == dataset) & (hp["train_load"] == load)]
        if hprow.empty:
            print(f"  !! sem hiperparametros para carga {load}", flush=True)
            continue
        h = hprow.iloc[0]

        preds = {
            m: (np.full(d.n, np.nan), np.zeros((len(folds), len(extra_test_idx))))
            for m in ("fcnn", "additive")
        }
        meta = {"fcnn": [], "additive": []}

        for f, held in enumerate(folds):
            pool = np.concatenate([folds[j] for j in range(len(folds)) if j != f])
            train_idx = pool[d.n_muts[pool] <= load]
            if len(train_idx) < 5:
                continue

            # --- FCNN ---
            model, ep_run, secs = fit_fcnn(
                d, train_idx, featurization,
                layer_size=int(h["layer_size"]),
                num_layers=int(h["num_layers"]),
                learning_rate=float(h["learning_rate"]),
                batch_size=int(h["batch_size"]),
                device=device, seed=seed + f, val_frac=val_frac, epochs=epochs,
            )
            preds["fcnn"][0][held] = predict_fcnn(model, d, held, featurization, device)
            if len(extra_test_idx):
                preds["fcnn"][1][f] = predict_fcnn(
                    model, d, extra_test_idx, featurization, device
                )
            meta["fcnn"].append((len(train_idx), ep_run, secs))
            del model

            # --- ridge aditivo, nos MESMOS folds ---
            amodel, alpha, asecs = fit_additive(d, train_idx)
            preds["additive"][0][held] = amodel.predict(
                np.asarray(d.X_mut[held].todense())
            )
            if len(extra_test_idx):
                preds["additive"][1][f] = amodel.predict(
                    np.asarray(d.X_mut[extra_test_idx].todense())
                )
            meta["additive"].append((len(train_idx), 0, asecs))

            print(f"  carga {load} fold {f}: n_treino={len(train_idx)} "
                  f"fcnn={ep_run}ep/{secs:.1f}s  ridge={asecs:.1f}s", flush=True)

        for mname in ("fcnn", "additive"):
            if not meta[mname]:
                continue
            cv_pred, extra = preds[mname]
            y_true, y_pred, loads = assemble_eval(
                d, cv_pred, extra.mean(axis=0), cv_pool_idx, extra_test_idx
            )
            if len(y_true) < 3:
                continue
            n_tr = int(np.median([m[0] for m in meta[mname]]))
            ep_med = int(np.median([m[1] for m in meta[mname]]))
            secs_tot = float(sum(m[2] for m in meta[mname]))

            def record(mask, label):
                pr, sr = corr(y_true[mask], y_pred[mask])
                rows.append({
                    "dataset": dataset,
                    "modelo": mname,
                    "featurizacao": featurization if mname == "fcnn" else "mut",
                    "carga_treino": load,
                    "carga_teste": label,
                    "n_treino": n_tr,
                    "n_teste": int(mask.sum()),
                    "entrada": d.input_dim(featurization) if mname == "fcnn"
                               else d.X_mut.shape[1],
                    "epocas_medianas": ep_med,
                    "segundos": round(secs_tot, 1),
                    "pearson": pr,
                    "spearman": sr,
                })

            record(np.ones(len(y_true), dtype=bool), "all")
            for k in sorted(set(loads.tolist())):
                km = loads == k
                if km.sum() >= 3:
                    record(km, str(int(k)))

    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, sep="\t", index=False)
    print(f"\nescrito: {out}  ({len(rows)} linhas)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset")
    ap.add_argument("--featurization", choices=FEATURIZATIONS)
    ap.add_argument("--array-index", type=int,
                    help="indice do array job; resolve conjunto e featurizacao")
    ap.add_argument("--list-jobs", action="store_true")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--val-frac", type=float, default=0.10)
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threads", type=int, default=0,
                    help="0 = usa SLURM_CPUS_PER_TASK ou o padrao do torch")
    args = ap.parse_args()

    if args.list_jobs:
        for i, (dsname, feat) in enumerate(array_jobs()):
            print(f"{i}\t{dsname}\t{feat}")
        return

    threads = args.threads or int(os.environ.get("SLURM_CPUS_PER_TASK", 0))
    if threads:
        torch.set_num_threads(threads)

    device_str = args.device
    if device_str == "auto":
        device_str = "cuda" if torch.cuda.is_available() else "cpu"

    if args.array_index is not None:
        jobs = array_jobs()
        if not 0 <= args.array_index < len(jobs):
            sys.exit(f"indice fora da faixa 0..{len(jobs) - 1}")
        dataset, featurization = jobs[args.array_index]
        out = Path(args.out_dir) / f"{dataset.replace(' ', '_')}_{featurization}.tsv"
    else:
        if not args.dataset or not args.featurization:
            sys.exit("informe --dataset e --featurization, ou --array-index")
        dataset, featurization = args.dataset, args.featurization
        out = Path(args.out) if args.out else (
            Path(args.out_dir) / f"{dataset.replace(' ', '_')}_{featurization}.tsv"
        )

    print(json.dumps({
        "dataset": dataset, "featurizacao": featurization, "device": device_str,
        "threads": threads or "padrao", "val_frac": args.val_frac,
        "epochs": args.epochs, "seed": args.seed,
    }, ensure_ascii=False), flush=True)

    run(dataset, featurization, Path(args.data_dir), out,
        device_str, args.val_frac, args.epochs, args.seed)


if __name__ == "__main__":
    main()
