#!/bin/bash
#SBATCH --job-name=nac-fcnn
#SBATCH --array=0-35
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
##SBATCH --account=SEU_PROJETO
##SBATCH --partition=SUA_PARTICAO
##SBATCH --gres=gpu:1
#
# EXPERIMENTO 5 — a FCNN DENTRO do Nulo Aditivo Calibrado.
#
# Fecha duas lacunas do capitulo:
#
#   (a) a objecao de revisor. A conclusao "epistasia especifica e pequena" repousa
#       num ridge pareado. A rede, calibrada contra o mesmo nulo, encontra mais?
#
#   (b) o numero central do capitulo nao esta calibrado. A vantagem da FCNN sobre
#       o aditivo em Pearson na interpolacao, +0,13, e a quantidade mais citada —
#       e nunca foi comparada contra o nulo.
#
# 36 TAREFAS = 12 conjuntos x 3 cargas de treino. Mapeamento (cargas em ordem
# decrescente, conjuntos por custo decrescente dentro de cada bloco):
#
#      0-11   carga 3     12-23   carga 2     24-35   carga 1
#
#   Confira com:  python src/calibrated_null_fcnn.py --list-jobs
#
# Todos os modelos rodam nos MESMOS folds e nas MESMAS paisagens simuladas:
# aditivo, epistasia global, FCNN e — nos 5 conjuntos identificaveis — ridge
# pareado. Os efeitos calibrados ficam diretamente comparaveis entre si.
#
# PRECISA DE PyTorch (ao contrario dos experimentos 2 e 3).
#
# CUSTO, ancorado nos tempos medidos do experimento 1 (featurizacao mut):
#   B=30   pior celula 4,6 h (GB1 carga 3)   soma das 36: 23 h
#   B=100  pior celula 15,4 h                soma das 36: 77 h
# B=30 e o padrao. O piso do p calibrado sobe para 1/31 = 0,0323, suficiente
# porque os efeitos em jogo (+0,13) sao ordens de magnitude maiores que a
# dispersao dos nulos observada ate agora.
#
# Com GPU descomente --gres; a rede e pequena, entao espere ganho modesto (ver a
# nota sobre overhead de kernel em RESULTADOS_MAPA.md).
#
# CONCESSAO DECLARADA: os hiperparametros sao os publicados na Tabela S3, FIXOS,
# e NAO reselecionados por replica — a armadilha 3.2 da ESPECIFICACAO nao e
# cumprida aqui, porque 72 configuracoes x 30 replicas x 36 celulas e impossivel.
# O vies resultante superestima o incremento de interacao da FCNN, logo trabalha
# contra a hipotese do capitulo. Ver o cabecalho de src/calibrated_null_fcnn.py.

set -euo pipefail
mkdir -p logs results_nac_fcnn

source .venv/bin/activate
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export PYTHONUNBUFFERED=1

REPLICAS="${NAC_REPLICAS:-30}"
SIGMA="${NAC_SIGMA:-maior_ordem}"

echo "tarefa ${SLURM_ARRAY_TASK_ID}  B=${REPLICAS}  sigma=${SIGMA}"
echo "em $(hostname) — $(date -Is)"
python src/calibrated_null_fcnn.py \
    --array-index "${SLURM_ARRAY_TASK_ID}" \
    --data-dir data \
    --replicates "$REPLICAS" \
    --sigma-unseen "$SIGMA" \
    --out-dir results_nac_fcnn \
    --device auto
echo "concluida — $(date -Is)"
