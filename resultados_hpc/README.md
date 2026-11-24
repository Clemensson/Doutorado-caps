# Resultados vindos do HPC

**Esta pasta é versionada.** É o destino curado das saídas do cluster.

Dentro de `hpc_fcnn_rerun/` os diretórios de trabalho (`results/`, `results_nac/`,
`results_sens/`, `results_global/`, `logs/`) são **ignorados pelo git** de
propósito: são saída bruta, regerável, e não devem poluir o histórico a cada
execução. Esta pasta é o oposto — o que entra aqui é resultado que o capítulo cita.

## Convenção

| Pasta | Experimento | Origem no cluster |
|---|---|---|
| `sens/` | 4 — sensibilidades (`val_frac`, `fold_seed`) | `hpc_fcnn_rerun/results_sens/` |
| `nac/` | 3 — Nulo Aditivo Calibrado | `hpc_fcnn_rerun/results_nac/` |
| `global/` | 2 — epistasia global | `hpc_fcnn_rerun/results_global/` |

O experimento 1 (reexecução da FCNN) está em `fcnn_resultados/` na raiz, por
precedência da primeira rodada.

## Fluxo no cluster

```bash
cd ~/Doutorado-caps/hpc_fcnn_rerun
sbatch slurm/nac.sbatch
# ... quando terminar:
cp results_nac/*.tsv   ../resultados_hpc/nac/
cp results_sens/*.tsv  ../resultados_hpc/sens/
mkdir -p ../resultados_hpc/nac/logs && cp logs/nac_*.out ../resultados_hpc/nac/logs/

cd ..
git add resultados_hpc
git commit -m "Resultados do HPC: <experimento>"
git push
```

Os `.tsv` são pequenos (KB a poucos MB). Os logs valem a pena por carregarem o
tempo de parede, a política de sigma e a semente de cada tarefa — é a procedência
que permite reconstruir qualquer número depois.

## Antes de commitar do cluster

Configura a identidade **com o e-mail noreply**, senão o GitHub recusa o push com
`GH007: Your push would publish a private email address`:

```bash
git config user.name  "Clemensson"
git config user.email "134302021+Clemensson@users.noreply.github.com"
```
