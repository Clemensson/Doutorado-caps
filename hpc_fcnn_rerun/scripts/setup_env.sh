#!/bin/bash
# Cria o ambiente. Rode da raiz do pacote: bash scripts/setup_env.sh
# Para CPU apenas (menor download), use o indice de CPU do PyTorch.
set -euo pipefail
PY="${PYTHON:-python3}"
"$PY" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
if [ "${CPU_ONLY:-0}" = "1" ]; then
    pip install --index-url https://download.pytorch.org/whl/cpu torch
    pip install numpy pandas scipy scikit-learn
else
    pip install -r requirements.txt
fi
python -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
