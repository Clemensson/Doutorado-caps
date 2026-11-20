# O protocolo de benchmarking de Tran et al., reconstruído

Reconstrução de 2026-11-20. Implementação em `src/aligned_protocol.py`.

O marco zero usou partições nossas, o que tornou a comparação com os números
publicados meramente indicativa. Este documento registra o protocolo original, para
que a comparação passe a ser pareada.

## Fontes e como elas se encaixam

Nenhuma das três fontes basta sozinha; juntas determinam o protocolo.

1. **`multievolve/utils/benchmark_utils.py::preprocess_dataset`** — o filtro de
   estringência. Com `stringency='singles'`, mantém apenas variantes cujas mutações
   constituintes **todas** existam como single mutante medido no conjunto. É o que
   produz as colunas "Post-filtering" da Tabela S7. Também ordena por
   `num_mutations` decrescente, o que importa porque afeta a composição dos folds.

2. **`multievolve/splitters/base_splitters.py::MutLoadProteinSplitter`** — corte por
   carga: treino em `load ≤ max_train_muts`, teste em `load ≥ min_test_muts`, com a
   assertiva `max_train_muts < min_test_muts`, descartando as cargas intermediárias.

3. **`multievolve-baselines/analysis/additive-proteingym_fig2ef.ipynb`** (DeWitt lab)
   — a reconstrução explícita da Fig. 2E/F.

### A contradição que a terceira fonte resolve

A Tabela S4 contém células com **carga de treino 3 e carga de teste 3**, o que viola
a assertiva de `MutLoadProteinSplitter`. Se as partições fossem um corte puro por
carga, essas células não poderiam existir.

A resolução: o benchmarking da Fig. 2E **não usa** o `MutLoadProteinSplitter`. Ele
usa um pool de validação cruzada. Variantes de carga 3 estão no pool, logo recebem
predição quando o fold em que estão é o retido — mesmo quando o treino inclui
cargas até 3.

## O protocolo

1. Filtro de estringência `'singles'`.
2. **Normalização min-max de `DMS_score` para [0, 1]**.
3. Features one-hot sobre as mutações pontuais distintas (equivalente à nossa matriz
   de desenho binária).
4. Partição: **pool de CV = cargas 1–3**; **teste extra = cargas ≥ 4**.
5. Pool de CV dividido em **5 folds**, com `np.random.seed(42)`.
6. Para cada carga máxima de treino L ∈ {1, 2, 3} e cada fold: ajustar nos variantes
   de carga ≤ L **dos outros 4 folds**; predizer o fold retido e o teste extra.
7. Variantes do pool de CV recebem a predição do fold em que foram retidos;
   variantes do teste extra recebem a **média das 5 predições**.
8. Avaliar em cargas ≥ 3: global (`all`) e estratificado por carga exata.

Ridge de referência: `RidgeCV(alphas=np.logspace(-3, 3, 50), fit_intercept=True)`,
com a seleção eficiente de α por LOO/GCV embutida no sklearn.

## Como o marco zero diferia

Cinco diferenças, todas corrigidas na implementação alinhada:

| Aspecto | Marco zero | Protocolo alinhado |
|---|---|---|
| Conjunto de teste | ordem ≥ 4 apenas | pool de CV com carga ≥ 3 **+** teste extra ≥ 4 |
| Treino | **todas** as variantes de ordem ≤ L | 4/5 delas (um fold sempre retido) |
| Escala de y | identidade | **min-max para [0, 1]** |
| Filtro | nenhum | estringência `'singles'` |
| Seleção de α | `cv=5` | LOO/GCV, grade de 50 valores |

A segunda linha é a mais relevante: o marco zero treinava com ~25% mais dados do que
o protocolo original, o que infla o desempenho do aditivo. A comparação pareada
corrige isso.

## Pendências da especificação que isto resolve

**§6, "Escala g(·) por conjunto" — RESOLVIDO.** O artigo normaliza por min-max para
[0, 1], não por log. Para os três conjuntos `Somermeyer_2022`, em brilho bruto, é
isso que explica como entram no benchmark sem transformação logarítmica.

Consequência metodológica que **permanece aberta e agora é mais interessante**:
min-max é uma transformação **afim**, logo preserva toda a estrutura de aditividade
e não endereça o argumento biofísico de que aditividade é esperada em escala
logarítmica. Spearman é invariante a transformações monotônicas, então a escolha não
afeta o ranqueamento; **Pearson sim**. Portanto:

> Replicar o protocolo em escala log, mantendo todo o resto igual, é um experimento
> de sensibilidade com valor próprio — e pode ser uma contribuição do Artigo 1. Se o
> aditivo melhorar em escala log enquanto a FCNN não, isso indica que parte da
> "epistasia" que a rede captura é apenas a não linearidade de escala que o modelo
> aditivo não pôde absorver por ter sido ajustado na escala errada.

Essa é epistasia global, não específica — e o desenho original não a separa.

**§6, "Tratamento de coeficientes não identificados" — RESOLVIDO por construção.** O
filtro de estringência `'singles'` garante que toda mutação presente em qualquer
variante retida também aparece como single medido. Logo não existem coeficientes não
identificados dentro do conjunto filtrado. A decisão de encolher a zero, que o marco
zero precisou tomar, deixa de ser necessária.

## Ressalva de fidelidade

`sort_values(by='num_mutations')` não garante a ordenação de empates entre
implementações (o original usa o padrão do pandas, não estável; usamos
`kind='stable'` para ser determinístico). A composição exata dos folds pode portanto
diferir da do notebook de referência. O efeito é de variabilidade amostral, não
sistemático, e é quantificável variando `--seed`. Isso deve ser reportado, não
escondido: é precisamente o tipo de variabilidade que o nulo calibrado existe para
medir.
