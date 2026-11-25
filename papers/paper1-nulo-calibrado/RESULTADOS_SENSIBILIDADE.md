# Artigo 1 — As duas sensibilidades

Execução no HPC em 25/11/2026, 144 tarefas. Resultados em `resultados_hpc/sens/`,
análise em `src/analyze_sensitivity.py`.

Fecha as duas ressalvas declaradas em `RESULTADOS_FCNN.md` §7. Ambas testam se
**escolhas nossas** estavam sustentando os números do capítulo.

---

## 1. Um bug de análise que quase passou

A primeira versão do script pareava FCNN e aditivo usando
`[dataset, featurizacao, carga_treino, carga_teste]` como chave. Mas o `run_one.py`
grava as linhas do aditivo **sempre** com `featurizacao='mut'`, porque o aditivo não
usa one-hot de sequência. Resultado: os 72 arquivos `seq` não encontravam par e eram
descartados **em silêncio** — 2.163 linhas em vez de 4.326, metade dos dados, sem
erro nem aviso.

Só apareceu porque a tabela saiu com uma featurização só. O script agora levanta
exceção se o pareamento perder qualquer linha.

---

## 2. Sensibilidade a `val_frac`

O *early stopping* exige validação, e o `val_split` de Tran et al. não está
documentado em nenhuma das três fontes. Adotamos 10%; aqui 5% e 20%.

Delta = FCNN − aditivo, unidade o conjunto. Positivo = a rede melhor.

| Featurização | Regime | 0,05 | 0,10 | 0,20 | Amplitude |
|---|---|---|---|---|---|
| **Pearson** | | | | | |
| `mut` | interpolação | 0,1338 | 0,1338 | 0,1319 | **0,0019** |
| `seq` | interpolação | 0,1175 | 0,1304 | 0,1282 | **0,0129** |
| `mut` | extrapolação | 0,0488 | 0,0448 | 0,0371 | 0,0118 |
| `seq` | extrapolação | 0,0361 | 0,0155 | 0,0223 | **0,0206** |
| **Spearman** | | | | | |
| `mut` | interpolação | 0,0217 | 0,0194 | 0,0258 | 0,0064 |
| `seq` | interpolação | 0,0224 | 0,0245 | 0,0238 | **0,0021** |
| `mut` | extrapolação | 0,0002 | −0,0106 | −0,0137 | **0,0140** |
| `seq` | extrapolação | −0,0024 | −0,0191 | −0,0132 | **0,0168** |

---

## 3. Variabilidade entre sementes de fold

Esta é a régua do capítulo: um efeito menor que o desvio entre sementes não é
distinguível de ruído de particionamento.

| Featurização | Regime | Média (5 sementes) | Desvio | Amplitude |
|---|---|---|---|---|
| **Pearson** | | | | |
| `mut` | interpolação | 0,1321 | **0,0042** | 0,0098 |
| `seq` | interpolação | 0,1283 | **0,0039** | 0,0096 |
| `mut` | extrapolação | 0,0435 | 0,0050 | 0,0131 |
| `seq` | extrapolação | 0,0265 | 0,0078 | 0,0186 |
| **Spearman** | | | | |
| `mut` | interpolação | 0,0223 | **0,0022** | 0,0058 |
| `seq` | interpolação | 0,0239 | **0,0011** | 0,0027 |
| `mut` | extrapolação | −0,0081 | 0,0059 | 0,0147 |
| `seq` | extrapolação | −0,0141 | 0,0068 | 0,0172 |

---

## 4. Os efeitos do capítulo contra a régua

| Efeito | Baseline | Média | Desvio | **Efeito / desvio** |
|---|---|---|---|---|
| Vantagem da FCNN em Pearson, interpolação (`mut`) | 0,1338 | 0,1321 | 0,0042 | **31,5** |
| Vantagem da FCNN em Pearson, interpolação (`seq`) | 0,1304 | 0,1283 | 0,0039 | **32,6** |
| Vantagem da FCNN em Spearman, interpolação (`seq`) | 0,0245 | 0,0239 | 0,0011 | **21,0** |
| Vantagem da FCNN em Spearman, interpolação (`mut`) | 0,0194 | 0,0223 | 0,0022 | **10,3** |
| Aditivo melhor na extrapolação, Spearman (`seq`) | −0,0191 | −0,0141 | 0,0068 | **2,1** |

---

## 5. O que sobrevive, e o que eu preciso retirar

### Sobrevive, com folga

**A vantagem da FCNN em Pearson na interpolação** (+0,13): **31 a 33 vezes** o desvio
entre sementes, e a amplitude por `val_frac` é de 1% a 10% do efeito. Inabalável.

**A vantagem da FCNN em Spearman na interpolação** (+0,02): 10 a 21 vezes o desvio.
Sólida.

**Logo a assimetria Pearson/Spearman — 0,13 contra 0,02 — que é o instrumento central
do capítulo, está sustentada.** Era o que mais importava testar.

### Não sobrevive

**A afirmação de que o aditivo é melhor na extrapolação.** Em `RESULTADOS_FCNN.md` §3
eu escrevi, em negrito, que "com a featurização fiel ao artigo (`seq`), o aditivo é
melhor em 10 de 12 conjuntos", com efeito de +0,0191.

Esse efeito é apenas **2,1 vezes** o desvio entre sementes, e a amplitude por
`val_frac` (0,0168) é **da mesma ordem do próprio efeito**. Em `val_frac` = 0,05 o
delta de `mut` na extrapolação chega a +0,0002, isto é, muda de sinal.

**Essa afirmação tem de ser retirada.** O que se sustenta é a versão em negativo, que
é também a que o capítulo precisa:

> Na extrapolação **não há vantagem demonstrável da FCNN sobre o aditivo**. Os efeitos
> são indistinguíveis de zero, e indistinguíveis da variabilidade de
> particionamento.

A diferença entre "o aditivo é melhor" e "a rede não é melhor" não é retórica. A
primeira é uma afirmação positiva que os dados não sustentam; a segunda é a ausência
de evidência, que é exatamente o ponto contra a atribuição de desempenho a epistasia.

---

## 6. Observação metodológica

As duas sensibilidades custaram 144 tarefas e confirmaram o resultado central
enquanto mataram uma afirmação secundária que eu havia apresentado em negrito. É o
que elas existiam para fazer.

Vale registrar a assimetria de custo: medir a variabilidade de particionamento exigiu
96 tarefas e revelou que um dos efeitos reportados estava a 2,1 desvios — na faixa em
que a conclusão depende da semente. Sem isso, o capítulo teria ido a banca com uma
afirmação frágil em negrito.
