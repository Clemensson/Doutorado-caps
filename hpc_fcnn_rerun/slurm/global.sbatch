#!/bin/bash
#SBATCH --job-name=ge-baseline
#SBATCH --array=0-11
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
##SBATCH --account=SEU_PROJETO
##SBATCH --partition=SUA_PARTICAO
#
# EXPERIMENTO 2 — baseline de epistasia global: y ~ g(x'beta), g monotonica.
#
# Uma tarefa por conjunto (12). NAO precisa de GPU nem de PyTorch: so numpy,
# scipy e sklearn. O indice 0 e o conjunto mais caro (config/datasets.tsv esta
# ordenado por custo decrescente), portanto a fila comeca pelo pior caso.
#
# Referencia de custo medida localmente: a execucao serial dos 12 conjuntos levou
# cerca de 2 h numa maquina de 6 nucleos. Como array, o tempo de parede e o
# conjunto mais lento (Phototropin, p=2122). As 4 h de --time sao folga.
#
# A predicao usa matriz esparsa; o pico de memoria e de ~17 MB, nao GB. Os 16G
# pedidos cobrem o treino denso (ate ~185 MB) com margem larga.

set -euo pipefail
mkdir -p logs results_global

source .venv/bin/activate
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export PYTHONUNBUFFERED=1

DATASET=$(awk -F'\t' 'NR>1 {print $1}' config/datasets.tsv \
          | sed -n "$((SLURM_ARRAY_TASK_ID + 1))p")
if [ -z "$DATASET" ]; then
    echo "indice ${SLURM_ARRAY_TASK_ID} nao mapeia para conjunto nenhum"; exit 1
fi
SAFE=${DATASET// /_}

echo "tarefa ${SLURM_ARRAY_TASK_ID} = ${DATASET} em $(hostname) — $(date -Is)"
python src/global_epistasis.py \
    --data-dir data \
    --datasets "$DATASET" \
    --out "results_global/${SAFE}.tsv"
echo "concluida — $(date -Is)"
