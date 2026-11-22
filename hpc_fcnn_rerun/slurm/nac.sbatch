#!/bin/bash
#SBATCH --job-name=nac
#SBATCH --array=0-4
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
##SBATCH --account=SEU_PROJETO
##SBATCH --partition=SUA_PARTICAO
#
# EXPERIMENTO 3 — Nulo Aditivo Calibrado.
#
# Simula B paisagens SEM epistasia, casadas ao conjunto real em desenho,
# composicao de ordens e razao sinal-ruido, e roda o pipeline inteiro em cada
# uma. A distribuicao resultante do ganho sobre o aditivo e o alvo de comparacao
# correto, em vez de zero.
#
# APENAS 5 CONJUNTOS. O modelo pareado tem p + p(p-1)/2 features, e isso so e
# estimavel onde p e pequeno (ver config/nac_datasets.tsv):
#
#     ParD3             p=37    ->     703 features
#     GB1               p=76    ->   2.926
#     TrpB              p=77    ->   3.003
#     IGP dehydratase   p=168   ->  14.196
#     NucB              p=221   ->  24.531
#
# Os outros sete passam de 95 mil features (scFv) a 2,25 MILHOES (Phototropin):
# inestimaveis, e nao por limite de maquina — nao ha dados que os identifiquem.
# Essa restricao e um resultado em si: um modelo de epistasia pareada so e
# ajustavel justamente nas paisagens de poucas posicoes, que sao as mesmas em que
# a densidade de duplos medidos por par de posicoes e alta.
#
# Custo medido localmente: ~63 s por replica em GB1 (p_pareado=2926,
# n_treino=28.186) numa maquina de 6 nucleos. Com B=50, cerca de 1 h por
# conjunto. NucB tem p_pareado=24.531 e deve ser bem mais caro: as 12 h de
# --time e a memoria de 48G existem por causa dele.
#
# Nao precisa de GPU nem de PyTorch.

set -euo pipefail
mkdir -p logs results_nac

source .venv/bin/activate
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export PYTHONUNBUFFERED=1

REPLICAS="${NAC_REPLICAS:-50}"
CARGA="${NAC_TRAIN_LOAD:-3}"

DATASET=$(awk -F'\t' 'NR>1 {print $1}' config/nac_datasets.tsv \
          | sed -n "$((SLURM_ARRAY_TASK_ID + 1))p")
if [ -z "$DATASET" ]; then
    echo "indice ${SLURM_ARRAY_TASK_ID} nao mapeia para conjunto nenhum"; exit 1
fi
SAFE=${DATASET// /_}

echo "tarefa ${SLURM_ARRAY_TASK_ID} = ${DATASET}  B=${REPLICAS}  carga=${CARGA}"
echo "em $(hostname) — $(date -Is)"
python src/calibrated_null.py \
    --data-dir data \
    --datasets "$DATASET" \
    --train-load "$CARGA" \
    --replicates "$REPLICAS" \
    --out "results_nac/${SAFE}_L${CARGA}.tsv"
echo "concluida — $(date -Is)"
