#!/bin/bash
# Baixa os 12 CSVs do Zenodo para data/ (375 MB). Requer internet no no de login.
# Se o cluster nao tiver internet, transfira data/ por rsync da maquina local:
#   rsync -av --progress data/external/zenodo-17620759/ USUARIO@HOST:CAMINHO/data/
set -euo pipefail
mkdir -p data
REC=17620759
BASE="https://zenodo.org/api/records/${REC}/files"
while IFS=$'\t' read -r dataset arquivo seq_len custo; do
    [ "$dataset" = "dataset" ] && continue
    if [ -s "data/${arquivo}" ]; then
        echo "ja existe: ${arquivo}"; continue
    fi
    echo "baixando ${arquivo}"
    curl -sL --fail --max-time 600 "${BASE}/${arquivo}/content" -o "data/${arquivo}"
done < config/datasets.tsv
echo "--- conteudo de data/ ---"
ls -lh data/
