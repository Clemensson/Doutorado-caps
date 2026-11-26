# Relatório de primeiro olhar — os 12 conjuntos DMS do benchmark

**Para:** a equipe, antes de decidir como modelar epistasia compensatória
**Data:** 26/11/2026
**Dados:** `data/external/zenodo-17620759/` (12 CSV, 375 MB, esquema ProteinGym)
**Código:** `exploratoria/src/`
**Tabelas:** `exploratoria/resultados/eda_*.tsv`

> **Sobre marcadores de estimativa:** a instrução pedia marcar como
> `[ESTIMATE PLACEHOLDER]` qualquer estatística não computável sem os dados reais.
> **Não há nenhum marcador neste relatório** — os 12 arquivos estão locais e toda
> estatística abaixo foi calculada sobre os dados completos, exceto a consistência
> sequência/mutação, que usa amostras estratificadas e está rotulada como tal.

---

## Veredicto, antes dos detalhes

A pergunta da equipe é epistasia compensatória: **combinações em que mutações
individualmente neutras ou deletérias produzem uma variante melhor que as partes.**

Dos 12 conjuntos, **apenas 4 sustentam a pergunta**, e por dois motivos
independentes que precisam ser verificados juntos: ter candidatos suficientes, e ter
as mutações constituintes medidas.

| Conjunto | Candidatos compensatórios | Multimutantes sem todas as partes medidas | Veredicto |
|---|---|---|---|
| **IGP dehydratase** (HIS7) | **1.534** (0,60%) | 48,7% | **usar** — maior número absoluto |
| **TrpB** | **375** (0,24%) | **0,0%** | **usar** — limpo |
| **ParD3** (F7YBW8) | 67 (**0,73%**) | **0,0%** | **usar** — maior taxa, n pequeno |
| **GB1** (SPG1) | 23 (0,02%) | **0,0%** | marginal — limpo mas raro |
| avGFP | 58 (0,14%) | 15,7% | marginal |
| amacGFP | 6 | 5,3% | não |
| ppluGFP2, cgreGFP, Phototropin | 1–2 | 3–13% | não |
| AAV2 VP1 | **0** | 0,0% | não |
| **scFv** (VH14) | **0** | **84,1%** | **descartar** — ver P3 |
| **NucB** (Q65J43) | **2** | **95,4%** | **descartar** — ver P2 |

**O sinal compensatório é raro em todo lugar: no melhor caso, 0,73% das
combinações.** Qualquer desenho de modelagem precisa partir disso — é um problema de
classe desbalanceada, não de regressão comum.

---

## 1. Estatísticas por coluna

Os 12 arquivos têm o mesmo esquema de 4 colunas. **Zero valores ausentes em qualquer
coluna de qualquer conjunto.** Zero `mutant` duplicado em qualquer conjunto.

| Coluna | Tipo | Observação |
|---|---|---|
| `mutant` | texto | tokens separados por `:`, formato `[AA][pos][AA]`; 16,9 a 44 caracteres |
| `mutated_sequence` | texto | **comprimento constante dentro de cada conjunto** (93 a 735 aminoácidos) |
| `DMS_score` | numérica | a medida fenotípica; escalas radicalmente diferentes (ver abaixo) |
| `DMS_score_bin` | binária | **derivada de `DMS_score`** — ver §3 |

### `DMS_score`, estatísticas exatas

| Conjunto | n | mín | máx | média | mediana | DP | IQR | MAD |
|---|---|---|---|---|---|---|---|---|
| HIS7 (IGP) | 496.137 | 0,00 | 2,33 | 0,619 | 0,879 | 0,449 | 0,995 | 0,163 |
| Phototropin | 167.529 | 0,02 | 1,78 | 0,640 | 0,632 | 0,293 | 0,452 | 0,226 |
| TrpB | 159.129 | 0,00 | 1,00 | 0,024 | 0,012 | 0,058 | 0,022 | 0,011 |
| GB1 (SPG1) | 149.360 | 0,00 | 8,76 | 0,081 | 0,003 | 0,395 | 0,008 | 0,003 |
| avGFP | 51.714 | 1,28 | 4,12 | 2,658 | 3,287 | 1,059 | 2,187 | 0,449 |
| AAV2 VP1 | 42.328 | −9,54 | 9,54 | −1,226 | −0,898 | 3,045 | 5,269 | 2,587 |
| scFv (VH14) | 35.889 | −6,71 | 2,42 | −1,626 | −1,066 | 1,905 | 3,406 | 1,355 |
| amacGFP | 33.510 | 449 | 18.689 | 6.303 | 7.430 | 3.485 | 5.411 | 1.822 |
| ppluGFP2 | 31.401 | 590 | 27.865 | 11.298 | 13.524 | 6.481 | 10.748 | 3.282 |
| cgreGFP | 24.515 | 590 | 40.087 | 13.076 | 9.933 | 12.531 | 25.159 | 9.343 |
| NucB (Q65J43) | 15.404 | 1,00 | 3,87 | 1,188 | **1,000** | 0,544 | **0,000** | **0,000** |
| ParD3 (F7YBW8) | 9.192 | −0,05 | 1,20 | 0,031 | −0,002 | 0,141 | 0,013 | 0,006 |

**Duas leituras importantes:**

**A escala varia seis ordens de magnitude** — IQR de 0,008 em GB1 contra 25.159 em
cgreGFP. Três conjuntos (os `Somermeyer_2022`) estão em intensidade bruta de
fluorescência; os demais em razões ou log. **Nenhum modelo pode ser treinado nos 12
sem normalização por conjunto declarada.**

**Média e mediana discordam fortemente em vários.** Em GB1 a média é 0,081 e a
mediana 0,003 — fator de 27. Em TrpB, 0,024 contra 0,012. Isso é cauda longa à
direita sobre uma massa concentrada perto do piso: a maioria das variantes é morta e
poucas são muito boas. **Usar média e DP nesses conjuntos induz erro; mediana, IQR e
MAD descrevem melhor.**

---

## 2. Distribuições

### A massa no piso do ensaio é o fato dominante

Fração de variantes exatamente no valor mínimo do conjunto:

| Conjunto | Massa no piso | Piso entre singles | Piso na ordem máxima |
|---|---|---|---|
| **NucB** | **87,0%** | **91,4%** | **100%** |
| cgreGFP | 31,9% | 7,7% | **100%** |
| **HIS7 (IGP)** | **29,8%** | 1,8% | **100%** |
| TrpB | 22,2% | 5,2% | 23,5% |
| GB1 | 19,7% | 0,0% | 20,7% |
| amacGFP | 2,7% | 0,3% | 0,0% |
| os outros 6 | < 1% | ~0 | ~0 |

Isto **não é ausência de dado** — é limite de detecção do ensaio. A distinção importa:
imputar ou descartar essas linhas falsificaria o fenômeno, que é "a variante está
morta", não "não medimos".

**Em 3 conjuntos, 100% das variantes de ordem máxima estão no piso.** Ou seja, acima
de certa carga mutacional o ensaio não discrimina mais nada. Modelar essas ordens é
ajustar ruído.

### O score cai com a ordem mutacional

A ordem máxima vai de 4 (GB1, TrpB, ParD3) a 43 (amacGFP). Em 11 dos 12 conjuntos a
distribuição desloca-se para baixo conforme a ordem cresce — quantificado na §3.

---

## 3. Correlações que merecem sinalização

### `DMS_score_bin` é função determinística de `DMS_score`

Testamos se o `bin` é um simples corte no score. **Coerência = 1,000 em todos os 12
conjuntos**, com limiares implícitos recuperados (por exemplo 2,4993 em avGFP, 0,3000
em HIS7, 12.499,53 em cgreGFP).

> **Consequência prática: a coluna `DMS_score_bin` não carrega informação
> independente.** Usá-la como atributo ao lado do score é redundância; usá-la como
> alvo enquanto o score está entre os atributos é **vazamento**. A fração de classe 1
> varia de 0,7% (TrpB) a 69,2% (amacGFP), então o limiar também não é comparável
> entre conjuntos.

### Score contra ordem mutacional: negativo em 11 de 12

| Conjunto | Spearman |
|---|---|
| avGFP | −0,546 |
| cgreGFP | −0,475 |
| ParD3 | −0,419 |
| Phototropin | −0,344 |
| ppluGFP2 | −0,282 |
| amacGFP | −0,248 |
| HIS7 | −0,204 |
| AAV2 VP1 | −0,156 |
| GB1 | −0,145 |
| TrpB | −0,100 |
| NucB | −0,037 |
| **scFv (VH14)** | **+0,670** |

Mais mutações, pior fenótipo — exceto **scFv, que é fortemente positivo**. Ver P3.

---

## 4. Problemas de dados

Ordenados por impacto na pergunta da equipe.

### P1 — Multimutantes cujas partes não foram medidas (crítico)

Para avaliar compensação é preciso conhecer o efeito de cada mutação isolada. Fração
de multimutantes em que ao menos uma mutação constituinte **não** tem single medido:

| Conjunto | Fração sem todas as partes |
|---|---|
| **NucB** | **95,4%** |
| **scFv** | **84,1%** |
| **HIS7 (IGP)** | **48,7%** |
| avGFP | 15,7% |
| cgreGFP | 13,4% |
| amacGFP | 5,3% |
| ppluGFP2 | 3,2% |
| **GB1, TrpB, ParD3, AAV2, Phototropin** | **0,0%** |

Em NucB, 95% dos multimutantes são **indecomponíveis** — a pergunta não pode ser feita
neles. No HIS7, que é o conjunto com mais candidatos em números absolutos, quase
metade é perdida.

### P2 — NucB está quase inteiramente censurado (crítico)

87% das variantes no piso, **IQR = 0 e MAD = 0**, mediana igual ao mínimo, e apenas
2.007 valores distintos em 15.404 linhas. Combinado com 95,4% de indecomponíveis,
**recomendamos descartar o NucB para esta pergunta.**

### P3 — scFv não parece uma varredura mutacional aleatória (crítico)

Duas anomalias que se reforçam: correlação score × ordem de **+0,670** (mais mutações,
*melhor*) e 84,1% de multimutantes indecomponíveis. O padrão é de uma biblioteca
**projetada ou selecionada** — variantes escolhidas por serem boas — não de
mutagênese sistemática. **Usar scFv como se fosse DMS aleatório enviesaria qualquer
conclusão sobre epistasia.** Zero candidatos compensatórios encontrados.

### P4 — Escalas incompatíveis entre conjuntos (alto)

Seis ordens de magnitude de diferença em IQR. Três conjuntos em intensidade bruta.
Qualquer análise conjunta exige normalização declarada e justificada por conjunto.

### P5 — Redundância e risco de vazamento em `DMS_score_bin` (médio)

Ver §3. É função determinística do score.

### P6 — Ordenação das linhas enviesa leitura parcial (médio)

O NucB está **ordenado crescentemente por ordem mutacional**: a média da ordem nas
1.000 primeiras linhas é 1,78 contra 8,29 no arquivo inteiro. scFv (2,87 contra 5,11)
e Phototropin (6,00 contra 7,98) também são enviesados. **Ler prefixo de arquivo —
`head`, `nrows`, limites de linha — produz amostra não representativa.** Por isso
construímos amostras estratificadas (`exploratoria/resultados/amostras/`, manifesto com
peso por estrato).

### P7 — Dois tokens malformados (desprezível)

Um em NucB e um em TrpB, de ~1,10 milhão de tokens verificados.

### O que NÃO é problema

Vale registrar, porque é incomum:

- **zero valores ausentes** em qualquer coluna de qualquer conjunto;
- **zero `mutant` duplicado** em qualquer conjunto;
- **comprimento de sequência constante** dentro de cada conjunto;
- **consistência mutação × sequência de 100%** sobre ~1,10 milhão de tokens
  verificados em amostras estratificadas: a posição e o aminoácido declarados no
  `mutant` sempre correspondem à `mutated_sequence`.

A qualidade mecânica dos dados é alta. Os problemas são **estruturais** — censura,
decomponibilidade, desenho de biblioteca — não de limpeza.

---

## 5. Próximos passos

Ligados diretamente à pergunta de epistasia compensatória.

### Decisões que recomendamos agora

1. **Restringir a 4 conjuntos:** HIS7 (IGP), TrpB, ParD3 e, marginalmente, GB1.
   Descartar NucB (P2) e scFv (P3) explicitamente e por escrito.
2. **Tratar como problema desbalanceado.** No melhor conjunto, 0,73% das combinações
   são candidatas. Métricas de regressão média vão esconder o fenômeno; é preciso
   precisão no topo, enriquecimento, ou classificação com classe rara.
3. **Excluir ordens totalmente censuradas.** Em HIS7 e cgreGFP, 100% da ordem máxima
   está no piso. Definir por conjunto a ordem acima da qual o ensaio não discrimina.
4. **Não usar `DMS_score_bin`** como atributo nem como alvo junto ao score (P5).
5. **Normalização por conjunto declarada** antes de qualquer análise conjunta (P4).

### Análises que faltam, em ordem de valor

| # | Análise | O que decide |
|---|---|---|
| 1 | Curva de `DMS_score` contra o preditor aditivo dos singles | **nomeia a forma da não linearidade**; fecha a lacuna aberta do Artigo 1 |
| 2 | Densidade de duplos medidos por par de posições | por que alguns conjuntos sustentam interação e outros não |
| 3 | Caracterizar os 1.534 candidatos do HIS7 | são posições específicas? contatos estruturais? um punhado de mutações recorrentes? |
| 4 | Verificar se "supera as partes" sobrevive ao ruído do ensaio | hoje é um corte determinístico sem incerteza |

A análise 1 continua sendo a de maior valor, e por um motivo preciso: a curva de
$y$ contra $x^\top\hat\beta$ **é** a função que um modelo de epistasia global aprende.

### Ressalva metodológica sobre as duas definições

As definições de `supera_as_partes` e `compensatorio` são **nossas e operacionais**,
declaradas em `exploratoria/src/eda_dominio.py`:

- `supera_as_partes` — score acima do maior single constituinte. Evita precisar de
  referência de tipo selvagem, que nem todo conjunto tem.
- `compensatorio` — todos os singles abaixo da mediana dos singles **e** combinação no
  decil superior do conjunto.

Nenhuma das duas incorpora **incerteza de medição**: são cortes determinísticos. Com
87% de massa no piso em alguns conjuntos, parte do que contamos como "supera as
partes" pode ser ruído. É a próxima coisa a endurecer (análise 4).

---

## Procedência e ferramental

| Item | Valor |
|---|---|
| Python | 3.12.10 (`.venv` do projeto) |
| Perfilamento genérico | skill `exploratory-data-analysis` v1.4 (K-Dense, MIT) |
| Amostras | estratificadas por ordem, semente `20261126`, piso de 200 por estrato |
| Dados brutos | abertos somente para leitura, não modificados |

A skill impôs três correções ao nosso procedimento, e vale registrar: (a) exigiu
manifesto antes de analisar conteúdo; (b) alertou que limitar linhas lê o prefixo e
não uma amostra — o que nos levou a **medir** o viés e encontrar o problema P6; e (c)
barrou nossa primeira tentativa de escrita porque o caminho de saída escapava do
`--root`.

Divergimos dela em dois pontos, deliberadamente: seus quantis vêm de uma subamostra de
512 elementos, e recalculamos exatos sobre os dados completos; e usamos
`--reveal-identifiers`, porque os dados são mutações de proteína, sem sujeito humano.

> **Citação exigida pela licença da skill**, caso ela contribua materialmente para um
> manuscrito: Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026).
> *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents.*
> arXiv:2609.00065. https://doi.org/10.48550/arXiv.2609.00065
