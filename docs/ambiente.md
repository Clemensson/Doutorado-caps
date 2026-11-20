# Ambiente computacional

Levantado em 2026-11-20, Windows 11.

## Disponível

| Ferramenta | Situação |
|---|---|
| git | 2.56.0.windows.4 |
| curl, awk, grep, sed | via Git Bash (`/ucrt64/bin`) |
| tar | `C:\Windows\system32\tar.exe` (lida com zip) |

## Ausente — e necessário

| Ferramenta | Situação | Para quê |
|---|---|---|
| **Python 3** | **ausente** | Tudo. O único Python instalado é o **2.7.11** do MGLTools (`C:\Program Files (x86)\MGLTools-1.5.7`), que não serve e não deve ser alterado. O comando `python3` no PATH é apenas o atalho da Microsoft Store, não um interpretador. |
| `gh` (GitHub CLI) | ausente | Criar e sincronizar o repositório remoto |
| R / Rscript | ausente | Não é requisito; só se houver preferência |

## Recomendação

O núcleo do projeto roda em **CPU** — 375 MB de dados, modelos aditivos, Ridge,
XGBoost e FCNNs pequenas (ver `data/README.md`, §3.5).

Para instalar, em ordem de preferência:

1. **Miniforge/conda** — o `multievolve-code` traz `env.yml`, feito para conda.
   É o caminho de menor resistência para reproduzir o ambiente original.
2. **Python 3.11+ oficial** com `venv`, se preferir evitar conda.

Cuidado ao instalar: **não mexer no Python 2.7 do MGLTools** — é parte de uma
instalação de ferramentas de docking, e quebrá-la tem custo colateral.

GPU só seria necessária para gerar embeddings de PLM no Artigo 2, e mesmo isso é
pré-computável uma vez e reutilizável.
