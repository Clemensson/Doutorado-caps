#!/bin/bash
#SBATCH --job-name=nac
#SBATCH --array=0-14
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
##SBATCH --account=SEU_PROJETO
##SBATCH --partition=SUA_PARTICAO
#
# EXPERIMENTO 3 — Nulo Aditivo Calibrado. O MAPA DE REGIMES do capitulo.
#
# Simula B paisagens SEM epistasia, casadas ao conjunto real em desenho,
# composicao de ordens e razao sinal-ruido, e roda o pipeline inteiro em cada uma.
# A distribuicao resultante do ganho sobre o aditivo e o alvo de comparacao
# correto, em vez de zero.
#
# 15 TAREFAS = 5 conjuntos x 3 cargas de treino. Esta e a entrega (2) revisada
# (ver ESPECIFICACAO.md secao 7.3): o mapa de regimes sobre os conjuntos em que
# ele e verificavel.
#
# Mapeamento do indice (cargas em ordem DECRESCENTE, para que as celulas mais
# informativas e mais caras entrem na fila primeiro):
#
#     0-4    carga de treino 3
#     5-9    carga de treino 2
#    10-14   carga de treino 1
#
#   e dentro de cada bloco, a ordem de config/nac_datasets.tsv:
#     ParD3, GB1, TrpB, IGP dehydratase, NucB
#
# POR QUE SO 5 CONJUNTOS. O modelo pareado tem p + p(p-1)/2 parametros:
#
#     ParD3             p=37    ->       703
#     GB1               p=76    ->     2.926
#     TrpB              p=77    ->     3.003
#     IGP dehydratase   p=168   ->    14.196
#     NucB              p=221   ->    24.531
#     ---------------------------------------- acima daqui, inestimavel
#     scFv              p=437   ->    95.703
#     AAV2 VP1          p=532   ->   141.778
#     avGFP..amacGFP    p~1100  ->  ~600.000
#     Phototropin       p=2122  -> 2.252.503
#
# Nao e limite de maquina: nao existem dados que identifiquem 2,25 milhoes de
# parametros de interacao a partir de alguns milhares de variantes. Epistasia
# pareada so e estimavel nas paisagens de poucas posicoes — que sao as mesmas em
# que a densidade de duplos medidos por par de posicoes e alta. Isso e um achado
# do capitulo, nao uma lacuna.
#
# CUSTO. Medido localmente: ~55 s por replica em GB1 (p_pareado=2.926,
# n_treino=28.186) em 6 nucleos; B=30 levou ~28 min. Cargas 1 e 2 tem treino
# menor e saem mais rapido.
#
# NAO e o p_pareado que governa o custo, e sim min(n_treino, p_pareado): o sklearn
# decompoe X^T X quando n > p e X X^T quando n < p, escolhendo sempre a matriz
# menor. Por isso:
#
#   NucB   p_pareado=24.531 mas n_treino=533   -> gram 533x533, TRIVIAL
#   IGP    p_pareado=14.196  e  n_treino=5.797 -> gram 5.797x5.797, o mais CARO
#   GB1    p_pareado=2.926   e  n_treino=28.186 -> covariancia 2.926x2.926
#
# Ou seja o conjunto mais pesado da fila e o IGP dehydratase, nao o NucB como
# parecia pelo numero de features. As 12 h de --time e os 48G cobrem o IGP.
#
# B=100 e o padrao aqui (contra 30 na rodada local) porque o p calibrado minimo e
# 1/(B+1): com 30 o piso era 0,032, com 100 vai a 0,0099.
#
# GB1 e TrpB na carga 3 ja foram rodados localmente com B=30; refazer com B=100
# da mais resolucao e serve de verificacao cruzada entre plataformas.
#
# Nao precisa de GPU nem de PyTorch.

set -euo pipefail
mkdir -p logs results_nac

source .venv/bin/activate
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export PYTHONUNBUFFERED=1

REPLICAS="${NAC_REPLICAS:-100}"
# Politica de sigma para ordens do teste ausentes do treino (a ordem 4 aqui).
# 'maior_ordem' e o padrao que produziu os resultados de 22/11; 'maior_sigma' e a
# variante conservadora da analise de sensibilidade. Ver RESULTADOS_NAC.md secao 5
# e sigma_para_ordens_nao_vistas em src/calibrated_null.py.
SIGMA="${NAC_SIGMA:-maior_ordem}"
N_CONJ=5

IDX="${SLURM_ARRAY_TASK_ID}"
CARGA=$(( 3 - IDX / N_CONJ ))
POS=$(( IDX % N_CONJ ))

if [ "$CARGA" -lt 1 ]; then
    echo "indice ${IDX} fora da faixa 0-14"; exit 1
fi

DATASET=$(awk -F'\t' 'NR>1 {print $1}' config/nac_datasets.tsv \
          | sed -n "$((POS + 1))p")
if [ -z "$DATASET" ]; then
    echo "indice ${IDX} nao mapeia para conjunto nenhum"; exit 1
fi
SAFE=${DATASET// /_}

echo "tarefa ${IDX} = ${DATASET} carga ${CARGA} B=${REPLICAS} sigma=${SIGMA}"
echo "em $(hostname) — $(date -Is)"
python src/calibrated_null.py \
    --data-dir data \
    --datasets "$DATASET" \
    --train-load "$CARGA" \
    --replicates "$REPLICAS" \
    --sigma-unseen "$SIGMA" \
    --out "results_nac/${SAFE}_L${CARGA}_${SIGMA}.tsv"
echo "concluida — $(date -Is)"
