# Artigo 1 — Escala e censura: de que natureza é a epistasia global?

Execução local, 25/11/2026. Código em `src/scale_and_censoring.py`, resultados em
`results/escala_censura.tsv`. Carga de treino 3.

Fecha a última pendência material da especificação, mas **não como ela foi
formulada**.

---

## 1. A pergunta estava mal posta, e inspecionar os dados mostrou por quê

A especificação previa "replicação em escala log", sob o argumento biofísico de que
efeitos mutacionais se somam em escala logarítmica quando são contribuições
termodinâmicas independentes.

O log é **impossível** na maioria dos conjuntos:

| Conjunto | Faixa | ≤ 0 | Natureza |
|---|---|---|---|
| ppluGFP2, amacGFP, cgreGFP | 449 – 40.087 | 0 | **intensidade bruta** — log bem posto |
| AAV2 VP1 | −9,5 – 9,5 | 23.935 | já está em log |
| scFv | −6,7 – 2,4 | 26.534 | já está em log |
| IGP dehydratase | 0 – 2,33 | 63.347 | zeros exatos em massa |
| TrpB | 0 – 1,00 | 35.250 | zeros exatos em massa |
| GB1 | 0 – 8,76 | 29.477 | zeros exatos em massa |

Dois conjuntos **já estão em log** — aplicar log de novo seria errado. E zeros exatos
em massa não são um problema de escala: são variantes no **piso do ensaio**, isto é
censura, e transformação monotônica nenhuma conserta censura.

Isso gerou uma hipótese alternativa minha: talvez a isotônica estivesse apenas
aprendendo o limite de detecção — mapeando uma faixa larga de valores latentes no
único valor zero. Formalmente epistasia global; biologicamente nada de termodinâmica.

Então a pendência virou duas perguntas.

---

## 2. Censura: a hipótese era minha, e está errada

Ganho da isotônica sobre o aditivo, no conjunto completo e restringindo às variantes
acima do piso:

| Conjunto | No piso | Ganho completo | Ganho acima do piso |
|---|---|---|---|
| TrpB | 22,2% | +0,2354 | **+0,2377** |
| GB1 | 19,7% | +0,2087 | +0,1858 |
| IGP dehydratase | 24,9% | +0,0260 | +0,0202 |
| **ParD3** | **0,0%** | **+0,3725** | +0,3725 |

**Remover as variantes do piso não derruba o ganho.** No `TrpB` ele sobe
ligeiramente. E a linha decisiva é a última: **`ParD3` tem o maior ganho de todos
(+0,37) com 1 variante no piso entre 9.192** — se a isotônica estivesse aprendendo o
limite de detecção, o conjunto que não tem limite de detecção não teria o maior ganho.

**Hipótese refutada.** A não linearidade monotônica é estrutura real da paisagem, não
artefato do ensaio.

Um detalhe que vale notar: no `IGP dehydratase` o aditivo cai de r = 0,755 para
0,505 ao remover o piso — as variantes mortas eram fáceis de predizer, e sustentavam
boa parte da correlação. Mas o **ganho** da isotônica quase não muda. É a distinção
entre explicar variância e explicar a *forma* da resposta.

### Correção de um número meu

Eu havia dito 148.064 zeros no `IGP dehydratase`, lido do CSV bruto. Depois do filtro
de estringência são **63.347 de 254.782** (24,9%): o filtro remove muitas variantes
mortas, porque as de ordem alta frequentemente contêm mutações que não foram medidas
como singles.

---

## 3. Escala: o log ajuda, mas explica a minoria

Nos três conjuntos de intensidade bruta, onde o log é bem posto:

| Conjunto | Aditivo (min-max) | Aditivo (log) | **Melhora do aditivo** |
|---|---|---|---|
| amacGFP | 0,8511 | 0,8883 | **+0,0372** |
| ppluGFP2 | 0,8662 | 0,8923 | **+0,0261** |
| cgreGFP | 0,7471 | 0,7537 | +0,0066 |

**O modelo aditivo melhora em escala log nos três conjuntos**, o que confirma o
argumento biofísico: parte da não aditividade é, de fato, ter ajustado na escala
errada.

Mas a quantidade que importa é se o **ganho da isotônica** encolhe:

| Conjunto | Ganho (min-max) | Ganho (log) | **Absorvido pelo log** |
|---|---|---|---|
| ppluGFP2 | +0,0701 | +0,0521 | **26%** |
| cgreGFP | +0,1982 | +0,1665 | **16%** |
| amacGFP | +0,0742 | +0,0631 | **15%** |

> **O log absorve de 15% a 26% da epistasia global. A maior parte não é
> logarítmica.**

Em Spearman, os ganhos são ~0 em todas as 14 configurações — consistente com a
invariância a transformações monotônicas, e aqui no regime rico em dados onde ela
vale (`RESULTADOS_MAPA.md` §4).

---

## 4. O que isto fecha

A natureza da epistasia global, por eliminação:

| Hipótese | Veredicto |
|---|---|
| Censura no piso do ensaio | **refutada** — o ganho sobrevive, e o maior está onde não há censura |
| Não linearidade logarítmica | **parcial** — explica 15% a 26% |
| Outra forma monotônica | **o que resta**, e é a maior parte |

A afirmação defensável:

> A estrutura não aditiva é real e monotônica. Ela **não** é limite de detecção, e é
> **apenas em parte** logarítmica. O resíduo é uma não linearidade monotônica de forma
> não identificada, e é a maior parte do efeito.

### A hipótese que o capítulo deixa aberta

Os três conjuntos onde o log é testável são todos de **fluorescência de GFP**, e a
resposta de fluorescência tem piso *e* teto — a fração dobrada satura em ambas as
pontas. Uma curva sigmoidal, do tipo Hill, descreveria isso e não é capturada por um
log, que só comprime a ponta alta.

Isso é **hipótese, não resultado**: testá-la exigiria ajustar uma família sigmoidal
paramétrica e comparar com a isotônica, o que não foi feito. Mas é a direção que os
dados apontam, e é biologicamente interpretável de um jeito que "não linearidade
monotônica genérica" não é.

> ✅ **CONFIRMADO VISUALMENTE em 26/11/2026** — `exploratoria/RESULTADO_ANALISE1.md`.
> Plotando o medido contra o previsto por um modelo aditivo nos 12 conjuntos, a forma
> é **sigmoide em 10 deles**: piso achatado, transição íngreme, saturação. E o
> mistério do log parcial se resolve — **o log comprime a cauda superior, mas o traço
> dominante é o piso inferior, e nenhuma função logarítmica produz um platô
> embaixo.** Duas exceções informativas: `Phototropin` é quase linear (e é onde o NAC
> não achou interação) e `TrpB` entorta para o outro lado, com retornos decrescentes.
>
> Continua sendo descrição visual, não ajuste: nenhuma sigmoide foi ajustada nem
> testada contra alternativas. O passo agora é trocar a isotônica por uma família
> paramétrica de 4 parâmetros, cujos valores teriam significado biofísico.
>
> Achado adicional que concorda com o NAC: o excesso de Spearman sobre Pearson separa
> os conjuntos em dois grupos, e os quatro com ρ < r — TrpB, NucB, ParD3, IGP — são
> exatamente aqueles em que o nulo calibrado encontrou interação específica.

---

## 5. Ressalvas

**Três conjuntos, uma família de ensaio.** O teste de escala só é bem posto nos três
GFPs de intensidade bruta. Se a forma da não linearidade for específica de
fluorescência, generalizar para os outros nove é injustificado.

**Uma carga de treino.** Carga 3 apenas.

**Dois conjuntos já em log não foram re-testados.** `AAV2 VP1` e `scFv` estão em
escala logarítmica na origem. Seria informativo *exponenciá-los* e verificar se a
epistasia global aumenta — o teste simétrico, que confirmaria a direção do efeito.
Não foi feito.

**Um bug que vale registrar.** A primeira versão deste módulo tentou realinhar os
valores brutos por posição depois do filtro de estringência. Não funciona: o filtro
remove linhas e os folds derivam da ordem delas, então o `y` logaritmizado ficava
pareado com as variantes erradas. A correção replica filtro e ordenação para carregar
o valor bruto na mesma ordem, com asserção de comprimento. Um erro desses não gera
exceção — gera um resultado plausível e errado.
