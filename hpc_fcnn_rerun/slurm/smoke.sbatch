#!/bin/bash
#SBATCH --job-name=fcnn-smoke
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/smoke_%j.out
#SBATCH --error=logs/smoke_%j.err
##SBATCH --account=SEU_PROJETO
##SBATCH --partition=SUA_PARTICAO
#
# Teste de fumaca: NucB (o conjunto mais barato, ~2,9 TFLOP no teto) com apenas
# 20 epocas. Valida ambiente, dados, dispositivo e formato de saida em poucos
# minutos, ANTES de gastar o array inteiro.
#
# Rode isto primeiro. Se passar, submeta slurm/array.sbatch.

set -euo pipefail
mkdir -p logs results_smoke

source .venv/bin/activate
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
export PYTHONUNBUFFERED=1

for feat in mut seq; do
    python src/run_one.py \
        --dataset NucB --featurization "$feat" \
        --data-dir data --out-dir results_smoke \
        --epochs 20 --device auto
done

echo "--- saida do teste de fumaca ---"
head -5 results_smoke/*.tsv
