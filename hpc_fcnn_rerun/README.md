# Reexecução da FCNN do MULTI-evolve — pacote para HPC

Pacote autocontido. Resolve a ressalva 5.1 de `RESULTADOS_ALINHADO.md`: até agora
comparamos **nosso** ridge aditivo contra a **FCNN publicada**, o que deixa aberta a
possibilidade de as diferenças vierem de detalhes de implementação em vez da classe
de modelo. Aqui os dois modelos rodam no **mesmo processo, nos mesmos folds**, o que
torna a comparação pareada de verdade.

Nada aqui importa do projeto pai — o diretório pode ser copiado isolado.

---

## 1. O que roda

**24 tarefas** = 12 conjuntos × 2 featurizações. Cada tarefa ajusta, para as cargas
de treino 1, 2 e 3, em 5 folds: a **FCNN** e o **ridge aditivo**, nos mesmos dados.

As duas featurizações:

| | Entrada | O que é |
|---|---|---|
| `seq` | 22 × L | One-hot da sequência inteira, 22 categorias por posição (20 aminoácidos + `*` + `X`). **É o que a FCNN publicada recebeu** (`OneHotFeaturizer` do MULTI-evolve). |
| `mut` | p | Indicador binário de mutação. É o que o baseline aditivo usa, e o que o notebook do DeWitt lab usou. |

As duas geram a **mesma classe de funções** — o one-hot de sequência é uma
transformação afim do indicador de mutação, já que nenhuma variante tem duas
substituições na mesma posição, e a primeira camada linear absorve a transformação.
O que difere é a geometria de otimização, a dimensão de entrada e como o *dropout*
age. O contraste entre as duas é portanto um resultado em si.

Hiperparâmetros: os **publicados**, extraídos da Tabela S3 (linhas `One-hot`) para
`config/hyperparams.tsv`. Não há varredura — refazê-la seria 12.960 ajustes em vez de
180, ou seja dias, e desnecessário já que o artigo publica os valores escolhidos.

---

## 2. Custo

Teto de 300 épocas, sem *early stopping* (o *early stopping* real deve cortar isso
para algo entre 1/3 e 1/5):

| | TFLOP |
|---|---|
| Featurização `seq` (12 conjuntos) | **1.281** |
| Featurização `mut` (12 conjuntos) | ~170 |
| **Total** | **~1.450** |

Por tarefa, do mais caro ao mais barato (`seq`; ver `config/datasets.tsv`):

| Conjunto | L | TFLOP |
|---|---|---|
| AAV2 VP1 | 735 | 321,6 |
| GB1 | 448 | 201,9 |
| TrpB | 389 | 179,3 |
| ppluGFP2 | 222 | 140,3 |
| avGFP | 238 | 132,3 |
| amacGFP | 238 | 127,5 |
| cgreGFP | 235 | 99,1 |
| IGP dehydratase | 220 | 29,1 |
| scFv | 246 | 27,7 |
| Phototropin | 118 | 13,8 |
| ParD3 | 93 | 5,5 |
| NucB | 142 | 2,9 |

**Como array job, o tempo de parede é a tarefa mais lenta, não a soma.**

- **CPU**: a pior tarefa (AAV2 VP1, 322 TFLOP) leva entre ~1 h e ~5 h, conforme a
  vazão real e o quanto o *early stopping* corta. O `--time=08:00:00` do script é
  folga deliberada.
- **GPU**: minutos. Se o cluster tiver GPU, **descomente `--gres=gpu:1`** — o código
  detecta e usa automaticamente (`--device auto`).

A incerteza na faixa de CPU é real: o gargalo são os *batch sizes* pequenos
(16 a 512 conforme o conjunto), que deixam o PyTorch limitado por overhead, não por
FLOPs. Rode o teste de fumaça primeiro para medir.

---

## 3. Como rodar

```bash
# 1. ambiente
bash scripts/setup_env.sh              # ou CPU_ONLY=1 bash scripts/setup_env.sh

# 2. dados (375 MB) — uma das duas vias
bash scripts/fetch_data.sh             # se o nó de login tiver internet
# ou, da máquina local:
#   rsync -av --progress data/external/zenodo-17620759/ USUARIO@HOST:CAMINHO/data/

# 3. validação sem PyTorch (segundos)
python -I scripts/selftest_data.py --data-dir data --dataset NucB

# 4. teste de fumaça — RODE ISTO ANTES DO ARRAY
sbatch slurm/smoke.sbatch              # NucB, 20 épocas, poucos minutos

# 5. array completo
sbatch slurm/array.sbatch

# 6. juntar e resumir
python src/merge.py --results-dir results --out merged.tsv
```

**Edite `slurm/array.sbatch` antes de submeter:** `--account`, `--partition`, a forma
de ativar o ambiente (módulos / conda / venv) e `--gres=gpu:1` se houver GPU.

As tarefas estão ordenadas por custo decrescente, então os índices 0 e 1 são
AAV2 VP1. Para rodar só os baratos primeiro: `sbatch --array=14-23 slurm/array.sbatch`.
Para listar o mapeamento: `python src/run_one.py --list-jobs`.

---

## 4. Saída

Uma TSV por tarefa em `results/`, com uma linha por (modelo × carga de treino ×
carga de teste), incluindo `all` e cada carga exata ≥ 3:

```
dataset  modelo  featurizacao  carga_treino  carga_teste  n_treino  n_teste
entrada  epocas_medianas  segundos  pearson  spearman
```

`src/merge.py` junta tudo e já reporta: Spearman global por modelo e carga; o delta
pareado (aditivo − FCNN) com Wilcoxon; a separação interpolação vs extrapolação; e o
custo efetivo medido. Ele **avisa se faltarem tarefas** do array.

---

## 5. O que este pacote reproduz, e o que desvia

### Reproduz fielmente

- Filtro de estringência `'singles'` (`preprocess_dataset` do MULTI-evolve)
- Normalização min-max de `DMS_score` para [0, 1]
- Partição: pool de CV = cargas 1–3, teste extra = cargas ≥ 4, 5 folds, semente 42
- Treino = variantes de carga ≤ L dos outros 4 folds; teste extra recebe a média das
  5 predições
- Arquitetura: `Linear(in,100) → LeakyReLU(0,2) → Dropout(0,2)`, repetido por camada
  oculta, saída `Linear(100,1)` — transcrita da classe `Fcn`
- `MSELoss`, Adam, 300 épocas, *early stopping* com paciência 15 e delta mínimo 10⁻⁵
- One-hot de sequência com 22 categorias
- Hiperparâmetros publicados na Tabela S3

### Desvia, declaradamente

**`val_split`.** O *early stopping* exige conjunto de validação, mas o `val_split` do
código original é `None` por padrão e **o valor usado no benchmarking da Fig. 2E não
está documentado em nenhuma das três fontes** (código, suplementar, notebook de
reanálise). Usamos 10% do subconjunto de treino, amostrado de forma estratificada por
carga mutacional (`--val-frac`, configurável). **A sensibilidade a essa escolha deve
ser reportada no artigo** — rodar com `--val-frac 0.05` e `0.20` é barato nos
conjuntos pequenos.

**Ordenação de empates.** `sort_values(by='num_mutations')` não garante ordem de
empates entre implementações; usamos `kind='stable'` para ser determinístico. A
composição exata dos folds pode diferir da do notebook de referência. É variabilidade
amostral, não viés, e é quantificável variando a semente.

**Ordem das categorias de aminoácido.** Irrelevante para um MLP (permutação das
features de entrada), portanto não reproduzida exatamente.

---

## 6. Estado de validação

| Componente | Estado |
|---|---|
| Sintaxe de todos os módulos | ✅ compila |
| Camada de dados (filtro, normalização, folds, ambas as featurizações, equivalência afim, determinismo) | ✅ 16/16 testes passam em NucB |
| Caminho PyTorch (FCNN, treino, *early stopping*) | ⚠️ **não executado** — PyTorch não está instalado na máquina onde o pacote foi montado |

**Por isso o teste de fumaça do passo 4 não é opcional.** Ele é a primeira execução
real do caminho de rede neural.
