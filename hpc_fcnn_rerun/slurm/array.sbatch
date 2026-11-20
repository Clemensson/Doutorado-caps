#!/bin/bash
#SBATCH --job-name=fcnn-rerun
#SBATCH --array=0-23
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
# ----------------------------------------------------------------------------
# EDITE ANTES DE SUBMETER:
#   --account / --partition conforme o cluster (linhas comentadas abaixo)
#   --gres=gpu:1 se houver GPU disponivel — reduz o tempo de horas para minutos
#
##SBATCH --account=SEU_PROJETO
##SBATCH --partition=SUA_PARTICAO
##SBATCH --gres=gpu:1
# ----------------------------------------------------------------------------
#
# 24 tarefas = 12 conjuntos x 2 featurizacoes ('seq' fiel ao artigo e 'mut'
# pareada ao aditivo). As tarefas sao ordenadas por custo decrescente, portanto
# os indices baixos sao os mais pesados (0 e 1 = AAV2 VP1).
#
# Tempo de parede = tarefa mais lenta, nao a soma. Em CPU, a pior tarefa
# (AAV2 VP1, one-hot de sequencia, ~322 TFLOP no teto de 300 epocas) deve levar
# algo entre 1 e 5 horas conforme a vazao real e o quanto o early stopping corta.
# As 8 horas de --time sao folga deliberada. Em GPU, minutos.

set -euo pipefail

mkdir -p logs results

# --- ambiente: adapte a UMA das tres opcoes ---
# (a) modulos do cluster
# module load python/3.11 cuda/12.1
# (b) conda
# source "$(conda info --base)/etc/profile.d/conda.sh" && conda activate fcnn-rerun
# (c) venv local (criado por scripts/setup_env.sh)
source .venv/bin/activate

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export PYTHONUNBUFFERED=1

echo "tarefa ${SLURM_ARRAY_TASK_ID} em $(hostname) — $(date -Is)"
python src/run_one.py \
    --array-index "${SLURM_ARRAY_TASK_ID}" \
    --data-dir data \
    --out-dir results \
    --device auto

echo "concluida — $(date -Is)"
