# Artigo 1 — O baseline de epistasia global

Execução local, 22/11/2026. Código em `src/global_epistasis.py`, comparação em
`src/compare_global_vs_fcnn.py`. Resultados em `results/global_epistasis.tsv`
(12/12 conjuntos, 1.035 linhas) e `results/comparacao_global_fcnn.tsv`.

**A pergunta.** A reexecução da FCNN mostrou que a vantagem da rede sobre o ridge
aditivo se concentra em Pearson e na interpolação (+0,134) e quase desaparece em
Spearman (+0,019). Como Spearman é invariante a transformação monotônica, isso
sugeria que o que a rede adquire é o *formato da curva de resposta* — epistasia
global, escala — e não interação entre mutações.

Este capítulo testa a hipótese com um modelo que **por construção não pode
representar interação nenhuma**:

$$y \sim g(x^\top\beta), \qquad g \text{ monotônica não decrescente}$$

Duas variantes: **dois estágios** (ridge, depois isotônica sobre $x^\top\beta$, sem
realimentação) e **conjunto** (minimização alternada entre $\beta$ e $g$).

---

## 1. A resposta: metade, não tudo

Ganho em Pearson sobre o aditivo puro. Unidade de análise o conjunto, n = 12.

| Regime | Modelo | Ganho | IC95 | Melhor que aditivo | Wilcoxon |
|---|---|---|---|---|---|
| **interpolação** | global 2 estágios | **+0,0667** | [+0,0289, +0,1046] | 10/12 | **p = 0,0024** |
| interpolação | global conjunto | +0,0676 | [+0,0155, +0,1197] | 10/12 | p = 0,0049 |
| interpolação | **FCNN (mut)** | **+0,1338** | [+0,0438, +0,2238] | 11/12 | p = 0,0015 |
| interpolação | FCNN (seq) | +0,1304 | [+0,0512, +0,2096] | 11/12 | p = 0,0010 |
| extrapolação | global 2 estágios | +0,0351 | [−0,0038, +0,0740] | 8/12 | p = 0,092 |
| extrapolação | global conjunto | +0,0344 | [−0,0129, +0,0818] | 8/12 | p = 0,233 |
| extrapolação | FCNN (mut) | +0,0421 | [−0,0046, +0,0888] | 8/12 | p = 0,266 |
| extrapolação | FCNN (seq) | +0,0128 | [−0,0282, +0,0539] | 8/12 | p = 0,519 |

> **Na interpolação, o modelo de epistasia global recupera cerca de 50% da vantagem
> da FCNN em Pearson** — 0,067 de 0,134 — com significância alta (p = 0,0024) e em 10
> dos 12 conjuntos. O ajuste conjunto não melhora nada sobre o de dois estágios
> (+0,0676 contra +0,0667), o que indica que a flexibilidade extra de reajustar
> $\beta$ não é o que importa aqui.

**Na extrapolação, nada é significativo para ninguém.** Nem a FCNN, nem o modelo
global, nem com uma featurização ou outra. No regime que o MULTI-evolve existe para
servir, nenhum modelo supera o aditivo puro de forma distinguível de ruído.

### Correção de um exagero meu

Durante a execução, o conjunto `ParD3` mostrou um ganho de +0,50 em Pearson e eu
disse que o modelo global "supera a FCNN com folga". **Isso estava errado como
afirmação geral.** `ParD3` é um caso extremo: 37 mutações, 4 posições. No agregado
sobre os 12 conjuntos, o modelo global recupera metade, não mais do que tudo.
Generalizei de um conjunto antes de ter os doze — exatamente o erro que a escolha do
conjunto como unidade de análise existe para evitar.

---

## 2. A invariância confirma a implementação

| Regime | Modelo | Ganho em Spearman | IC95 | Wilcoxon |
|---|---|---|---|---|
| interpolação | **global 2 estágios** | **−0,0023** | [−0,0043, −0,0003] | p = 0,0024 |
| extrapolação | global 2 estágios | −0,0108 | [−0,0229, +0,0012] | p = 0,110 |
| interpolação | global conjunto | +0,0060 | [−0,0246, +0,0367] | p = 0,850 |
| interpolação | FCNN (mut) | +0,0194 | [−0,0076, +0,0464] | p = 0,077 |
| interpolação | FCNN (seq) | +0,0245 | [+0,0013, +0,0476] | p = 0,021 |

O modelo de dois estágios **não ganha Spearman** — ganha −0,0023, ou seja perde
dois milésimos, exatamente o que se espera dos empates que os patamares da isotônica
criam. Nos valores por conjunto a coincidência vai a quatro casas decimais: ParD3
0,4143 → 0,4150; GB1 0,4725 → 0,4720; cgreGFP 0,8245 → 0,8245; avGFP 0,8561 →
0,8560.

Isso é a invariância de Spearman a transformações monotônicas se manifestando
numericamente, e serve como **checagem de validade interna da implementação**: se o
dois estágios tivesse ganhado Spearman, haveria um erro no código.

---

## 3. O que sobra, e não é escala

Dois fatos que a hipótese de epistasia global **não** explica:

1. **Metade da vantagem em Pearson na interpolação.** 0,134 da FCNN contra 0,067 do
   modelo global. O resíduo de ~0,067 não é transformação de escala.
2. **A FCNN ganha Spearman na interpolação** (+0,019 com `mut`, +0,025 com `seq`,
   p = 0,021) e o modelo global não (−0,002). Ganho de ordenamento não pode vir de
   uma transformação monotônica, por definição.

Portanto a conclusão correta é **calibrada, não categórica**:

> Cerca de metade do que parecia aprendizado de epistasia na interpolação é efeito de
> escala, reproduzível por um modelo sem nenhuma capacidade de interação. A outra
> metade, mais um pequeno ganho de ordenamento, não é — e é candidata a interação
> genuína, ainda que de magnitude modesta.

"A FCNN aprende apenas escala" é uma afirmação forte demais para os dados. O que se
sustenta é que **metade da evidência atribuída a epistasia se dissolve** quando se
compara contra o nulo certo.

---

## 4. O truncamento explica a fraqueza na extrapolação

$g$ é aprendida apenas na faixa de $x^\top\beta$ observada no treino. Variantes fora
dela são necessariamente truncadas:

| Modelo | Carga de treino | Fração truncada (média) | Máxima |
|---|---|---|---|
| global 2 estágios | 1 | **0,494** | 0,846 |
| global 2 estágios | 2 | 0,143 | 0,951 |
| global 2 estágios | 3 | 0,072 | 0,978 |
| global conjunto | 3 | 0,047 | 0,523 |

Com carga de treino 1, **metade das variantes de teste cai fora do domínio de $g$**.
Mesmo na carga 3, há conjuntos com 98% truncado. Um modelo de epistasia global **não
consegue extrapolar a própria não linearidade** — e isso impõe um teto ao que ele
pode recuperar justamente no regime de extrapolação, o que é consistente com o ganho
não significativo da §1.

Essa limitação é estrutural, não um defeito de implementação, e vale como resultado:
qualquer modelo de epistasia global herda esse teto.

---

## 5. Heterogeneidade entre conjuntos

Pearson na avaliação global, carga de treino 3:

| Conjunto | Aditivo | FCNN (mut) | Global conjunto |
|---|---|---|---|
| GB1 | 0,374 | **0,920** | 0,604 |
| TrpB | 0,470 | **0,932** | 0,758 |
| ParD3 | 0,426 | 0,878 | **0,927** |
| avGFP | 0,808 | 0,921 | **0,936** |
| IGP dehydratase | 0,755 | 0,762 | **0,800** |
| cgreGFP | 0,747 | **0,958** | 0,924 |
| amacGFP | 0,851 | **0,942** | 0,887 |
| ppluGFP2 | 0,866 | **0,942** | 0,913 |
| Phototropin | 0,838 | 0,836 | 0,833 |
| NucB | 0,298 | 0,262 | 0,296 |
| scFv | 0,765 | 0,769 | 0,770 |
| AAV2 VP1 | 0,639 | **0,767** | 0,658 |

Dois padrões merecem investigação:

**`GB1` e `TrpB` são onde a FCNN mais ganha além da escala** — +0,55 e +0,46 sobre o
aditivo, enquanto o modelo global recupera apenas +0,23 e +0,29. São as duas
paisagens combinatórias **quase completas em 4 posições** (99,5% e 93,4%). Isso é
coerente com epistasia específica real: em 4 posições com 19 substituições cada, a
densidade de duplos medidos por par de posições é altíssima, portanto há informação
de interação de fato estimável. **São os candidatos prioritários para o Nulo Aditivo
Calibrado.**

**`Phototropin`, `scFv` e `NucB` não mostram ganho para ninguém** — nem FCNN, nem
global. Nesses, o aditivo puro é o teto.

---

## 6. Ressalva de reprodutibilidade confirmada

A checagem de consistência embutida no comparador reporta: desvio do aditivo entre
este módulo e a execução no HPC de **5,00 × 10⁻¹⁵ nas cargas 2 e 3**, e
**1,42 × 10⁻¹ na carga 1**.

É a subdeterminação documentada em `RESULTADOS_FCNN.md` §6 se manifestando de novo,
agora com magnitude maior (0,14). Reforça: **a carga de treino 1 não é reproduzível
entre plataformas e não deve ser reportada com precisão decimal.**

---

## 7. Próximos passos

O capítulo tem agora três resultados encadeados: a FCNN não bate o aditivo na
extrapolação; metade da sua vantagem em Pearson na interpolação é escala; e o resíduo
concentra-se nas duas paisagens combinatórias quase completas.

1. **Nulo Aditivo Calibrado**, aplicado primeiro a `GB1` e `TrpB` — onde há o resíduo
   de ~0,067 em Pearson e o ganho de Spearman a explicar. É o único lugar com sinal
   que sobrevive ao baseline de escala.
2. **Sensibilidade a `val_split`** (0,05 / 0,10 / 0,20) e **a sementes de fold**.
   Pendência declarada desde `RESULTADOS_FCNN.md`; nenhuma foi medida ainda. ×15 o
   custo de uma rodada, portanto obrigatoriamente no HPC.
3. **Replicação em escala log.** Interage diretamente com a §1: se o aditivo for
   ajustado na escala em que a aditividade é biofisicamente esperada, parte dos 0,067
   de resíduo pode desaparecer sem modelo nenhum.
