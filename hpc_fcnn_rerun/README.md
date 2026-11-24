# Pacote HPC — Artigo 1

Pacote autocontido com os **quatro experimentos** do Capítulo 1. Nada importa do
projeto pai; o diretório pode ser copiado isolado.

| # | Experimento | Tarefas | Precisa torch? | Estado |
|---|---|---|---|---|
| 1 | Reexecução da FCNN | 24 | **sim** | ✅ concluído 22/11 |
| 2 | Baseline de epistasia global | 12 | não | pronto para submeter |
| 3 | Nulo Aditivo Calibrado — **o mapa de regimes** | **15** | não | pronto para submeter |
| 4 | Sensibilidades (`val_frac`, `fold_seed`) | 144 | **sim** | pronto para submeter |

Ordem recomendada: **4 primeiro** (fecha as ressalvas que bloqueiam a submissão),
depois **3** (o resultado novo), depois **2** se quiser reproduzir o baseline no
cluster — ele já rodou localmente.

---

## Preparação, uma vez

```bash
bash scripts/setup_env.sh          # ou CPU_ONLY=1 para experimentos 2 e 3
bash scripts/fetch_data.sh         # 375 MB; ou rsync da máquina local
python -I scripts/selftest_data.py --data-dir data --dataset NucB   # 16 testes
```

**Edite cada `.sbatch` antes de submeter:** `--account`, `--partition`, a forma de
ativar o ambiente, e `--gres=gpu:1` nos experimentos 1 e 4 se houver GPU.

---

## Experimento 1 — Reexecução da FCNN ✅

```bash
sbatch slurm/smoke.sbatch     # obrigatório antes do array
sbatch slurm/array.sbatch     # 24 tarefas = 12 conjuntos x 2 featurizações
python src/merge.py --results-dir results --out merged.tsv
```

Concluído: 132 min de treino somados, pior tarefa 23,8 min, épocas efetivas 56 na
mediana. Resultado em `RESULTADOS_FCNN.md` no projeto.

---

## Experimento 2 — Baseline de epistasia global

Modelo $y \sim g(x^\top\beta)$ com $g$ monotônica não decrescente. Por construção
**não pode representar interação nenhuma**. Duas variantes: dois estágios (ridge,
depois isotônica) e ajuste conjunto por minimização alternada.

```bash
sbatch slurm/global.sbatch        # 12 tarefas, uma por conjunto
```

Saída em `results_global/`. Já rodou localmente (ver
`RESULTADOS_EPISTASIA_GLOBAL.md`): recupera ~50% da vantagem da FCNN em Pearson na
interpolação, p = 0,0024.

---

## Experimento 3 — Nulo Aditivo Calibrado

Simula B paisagens **sem epistasia**, casadas ao conjunto real em desenho,
composição de ordens mutacionais e razão sinal-ruído, e roda o pipeline inteiro em
cada uma. A distribuição resultante do ganho sobre o aditivo é o alvo de comparação
correto, em vez de zero.

É a **entrega (2) revisada** do capítulo (ver `ESPECIFICACAO.md` §7.3): o mapa de
regimes sobre os conjuntos em que ele é verificável. **15 tarefas = 5 conjuntos × 3
cargas de treino**, com B = 100 réplicas.

```bash
sbatch slurm/nac.sbatch                      # as 15 células, B=100
sbatch --array=0-4 slurm/nac.sbatch          # só a carga 3 (as mais informativas)
NAC_REPLICAS=30 sbatch slurm/nac.sbatch      # mais rápido, p mínimo 0,032
NAC_SIGMA=maior_sigma sbatch slurm/nac.sbatch   # variante de sensibilidade
```

**`NAC_SIGMA`** controla o σ atribuído a ordens do teste ausentes do treino — a
ordem 4, aqui. Não é escolha neutra: nos conjuntos medidos os σ **decrescem** com a
ordem (GB1: 0,0926 / 0,0617 / 0,0502), então o padrão `maior_ordem` entrega ao nulo o
ruído mais limpo disponível, o que favorece o efeito observado. `maior_sigma` é o
caso oposto e mais conservador. É a ressalva mais relevante de `RESULTADOS_NAC.md`
§5. O nome da política entra no nome do arquivo de saída, então as duas rodadas
coexistem sem sobrescrever.

Mapeamento do índice — cargas em ordem decrescente, para as células mais caras e
informativas entrarem na fila primeiro:

| Índices | Carga de treino |
|---|---|
| 0–4 | 3 |
| 5–9 | 2 |
| 10–14 | 1 |

e dentro de cada bloco a ordem de `config/nac_datasets.tsv`: ParD3, GB1, TrpB,
IGP dehydratase, NucB.

B = 100 porque o p calibrado mínimo é 1/(B+1): com 30 o piso é 0,032, com 100 vai a
0,0099. GB1 e TrpB na carga 3 já rodaram localmente com B = 30 — refazer com 100 dá
resolução maior e serve de verificação cruzada entre plataformas.

Modelos calibrados: `additive` (controle — seu ganho sobre si mesmo deve ser
exatamente zero), `pairwise` (ridge com todas as interações pareadas — o teste
direto de epistasia **específica**) e `global_iso` (o baseline de escala).

### Só 5 conjuntos, e isso é um resultado

O modelo pareado tem $p + p(p-1)/2$ features:

| Conjunto | p | p pareado | Elegível |
|---|---|---|---|
| ParD3 | 37 | 703 | ✅ |
| GB1 | 76 | 2.926 | ✅ |
| TrpB | 77 | 3.003 | ✅ |
| IGP dehydratase | 168 | 14.196 | ✅ |
| NucB | 221 | 24.531 | ✅ |
| scFv | 437 | 95.703 | ✖ |
| AAV2 VP1 | 532 | 141.778 | ✖ |
| avGFP … amacGFP | 1.084–1.201 | 588k–722k | ✖ |
| Phototropin | 2.122 | **2.252.503** | ✖ |

Os sete excluídos não são limitação de máquina: **não há dados que identifiquem
tantos parâmetros de interação.** Um modelo de epistasia pareada só é ajustável nas
paisagens de poucas posições — que são justamente as mesmas em que a densidade de
duplos medidos por par de posições é alta. Vale como achado do capítulo.

Custo medido: ~63 s por réplica em GB1 numa máquina de 6 núcleos. `NucB`, com
24.531 features pareadas, deve ser muito mais caro — daí `--time=12:00:00` e 48G.

---

## Experimento 4 — As sensibilidades pendentes

Duas ressalvas declaradas em `RESULTADOS_FCNN.md` que **nunca foram medidas** e
precisam estar fechadas antes de submeter.

```bash
sbatch --array=0-47   slurm/sensibilidade.sbatch   # val_frac
sbatch --array=48-143 slurm/sensibilidade.sbatch   # fold_seed
sbatch slurm/sensibilidade.sbatch                  # ambas, 144 tarefas
```

**`val_frac`** (48 tarefas). O *early stopping* exige validação, mas o `val_split`
usado por Tran et al. não está documentado em nenhuma das três fontes. Adotamos
10%; aqui medimos 5% e 20%.

**`fold_seed`** (96 tarefas). Toda a análise usou uma única semente de
particionamento (42). Quatro sementes adicionais dão a variabilidade amostral dos
folds — exatamente a grandeza contra a qual os efeitos de 0,02 a 0,13 de Spearman
precisam ser julgados.

O grid (`config/jobs_sensibilidade.tsv`) varia **um fator por vez** a partir do
baseline já rodado. Produto cartesiano seria 360 tarefas e não responderia melhor
nenhuma das duas perguntas.

Nota: `--seed` do `run_one.py` semeia a inicialização da rede e a divisão de
validação; `--fold-seed` semeia o **particionamento**. São fatores distintos, e é o
segundo que mede variabilidade de folds.

---

## O que o pacote reproduz, e o que desvia

Fielmente: filtro de estringência `'singles'`; normalização min-max de `DMS_score`
para [0,1]; partição pool-de-CV (cargas 1–3) mais teste extra (≥4) em 5 folds com
semente 42; treino nas variantes de carga ≤ L dos outros 4 folds; média das 5
predições no teste extra; arquitetura `Linear→LeakyReLU(0,2)→Dropout(0,2)` por
camada com saída `Linear(100,1)`; `MSELoss`, Adam, 300 épocas, paciência 15 e delta
mínimo 10⁻⁵; one-hot de sequência com 22 categorias; hiperparâmetros da Tabela S3.

Desvios declarados:

- **`val_split`** não documentado na fonte — adotamos 10%, e o experimento 4 mede a
  sensibilidade.
- **Ordenação de empates** em `sort_values` usa `kind='stable'` para ser
  determinística; pode diferir do notebook de referência. Variabilidade amostral,
  não viés, e o experimento 4 a quantifica.
- **Ruído do nulo em ordens ausentes do treino** (ordem 4): usamos o sigma da maior
  ordem disponível no treino. Aproximação declarada em `src/calibrated_null.py`.
- **Ordem das categorias de aminoácido** é irrelevante para um MLP (permutação das
  features de entrada) e não foi reproduzida exatamente.

### Uma ressalva de reprodutibilidade que vale repetir

Na carga de treino 1, **n_treino/p = 0,80 por construção** em todo conjunto: o
filtro de estringência faz p = número de singles, e o treino são 4/5 deles. O
sistema é subdeterminado, o α colapsa no piso da grade em 8 dos 12 conjuntos, e os
valores **não são reproduzíveis entre plataformas** — observamos divergência de até
0,14 entre o HPC e a máquina local, enquanto as cargas 2 e 3 batem a 5 × 10⁻¹⁵. Não
reporte a carga 1 com precisão decimal.

---

## Estado de validação

| Componente | Estado |
|---|---|
| Sintaxe de todos os módulos | ✅ compila |
| Camada de dados | ✅ 16/16 testes em NucB |
| Mapeamento índice→conjunto dos arrays | ✅ testado, inclusive nomes com espaço e índice fora da faixa |
| Resolução do manifesto de sensibilidade | ✅ testada nos índices 0, 47, 48, 143 |
| Caminho PyTorch (experimentos 1 e 4) | ✅ validado pela execução do experimento 1 |
| Experimentos 2 e 3 | ✅ executados localmente antes de portar |
