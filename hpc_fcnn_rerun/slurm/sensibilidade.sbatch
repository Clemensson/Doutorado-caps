#!/bin/bash
#SBATCH --job-name=fcnn-sens
#SBATCH --array=0-143
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
##SBATCH --account=SEU_PROJETO
##SBATCH --partition=SUA_PARTICAO
##SBATCH --gres=gpu:1
#
# EXPERIMENTO 4 — as duas sensibilidades pendentes do capitulo.
#
# Ambas sao ressalvas declaradas em RESULTADOS_FCNN.md que nunca foram medidas, e
# ambas precisam estar fechadas antes de submeter.
#
#   val_frac (48 tarefas, indices 0-47)
#     O early stopping exige conjunto de validacao, mas o val_split usado por
#     Tran et al. NAO esta documentado em nenhuma das tres fontes (codigo,
#     suplementar, notebook de reanalise). Adotamos 10%. Aqui medimos 5% e 20%
#     para saber se a conclusao depende dessa escolha nossa.
#
#   fold_seed (96 tarefas, indices 48-143)
#     Toda a analise usou uma unica semente de particionamento (42). Quatro
#     sementes adicionais dao a variabilidade amostral dos folds, que e
#     exatamente a grandeza contra a qual os efeitos de ~0,02 a 0,13 de Spearman
#     precisam ser julgados.
#
# O grid esta em config/jobs_sensibilidade.tsv, um fator variado por vez a partir
# do baseline (val_frac=0.10, fold_seed=42) que ja foi rodado. Produto cartesiano
# seria 360 tarefas e nao responderia melhor nenhuma das duas perguntas.
#
# Custo: cada tarefa equivale a uma do experimento 1, onde 24 tarefas somaram
# 95 min de treino e a pior levou 23 min. Como array, o tempo de parede e a pior
# tarefa. Se houver GPU, descomente --gres e cai para minutos.
#
# Para rodar so uma das duas:  sbatch --array=0-47   slurm/sensibilidade.sbatch
#                              sbatch --array=48-143 slurm/sensibilidade.sbatch

set -euo pipefail
mkdir -p logs results_sens

source .venv/bin/activate
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export PYTHONUNBUFFERED=1

echo "tarefa ${SLURM_ARRAY_TASK_ID} em $(hostname) — $(date -Is)"
python src/run_one.py \
    --job-index "${SLURM_ARRAY_TASK_ID}" \
    --data-dir data \
    --out-dir results_sens \
    --device auto
echo "concluida — $(date -Is)"
