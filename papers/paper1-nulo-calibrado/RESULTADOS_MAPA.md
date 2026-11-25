# Artigo 1 — O mapa de regimes

Execução no HPC em 25/11/2026. **15 de 15 células** (5 conjuntos × 3 cargas de
treino), B = 100 réplicas, política de σ `maior_ordem`. Resultados em
`resultados_hpc/nac/`, análise em `src/analyze_nac_map.py`.

É a **entrega (2)** do capítulo (`ESPECIFICACAO.md` §7.3). A pergunta que o mapa
responde:

> Em que regime o incremento de epistasia **específica** sobre um modelo de escala
> sobrevive à calibração contra o nulo aditivo?

Com B = 100, o p calibrado mínimo é 1/101 = **0,0099**.

---

## 1. O número central: o incremento da interação

$\text{incremento} = \text{efeito}(\text{pareado}) - \text{efeito}(\text{global})$

Positivo significa que o modelo que **pode** representar interação supera o que
**não pode**, depois de ambos serem calibrados contra o nulo aditivo.

### Pearson

| Conjunto | Carga 1 | Carga 2 | Carga 3 |
|---|---|---|---|
| ParD3 | −0,029 | −0,368 | **−0,502** |
| GB1 | +0,035 | **+0,235** | +0,041 |
| TrpB | −0,025 | −0,058 | −0,178 |
| IGP dehydratase | −0,001 | +0,084 | −0,017 |
| NucB | +0,039 | +0,078 | +0,079 |

### Pearson, separado por regime na carga 3

| Conjunto | Interpolação | Extrapolação |
|---|---|---|
| ParD3 | **+0,132** | −0,527 |
| GB1 | **+0,172** | +0,030 |
| TrpB | **+0,089** | −0,262 |
| IGP dehydratase | **+0,023** | −0,018 |
| NucB | **+0,025** | +0,109 |

**Na interpolação o incremento é positivo em 5 de 5 conjuntos.** Na extrapolação é
inconsistente, e fortemente negativo em dois.

### Spearman, carga 3

| Conjunto | Interpolação | Extrapolação |
|---|---|---|
| ParD3 | −0,048 | −0,520 |
| GB1 | −0,137 | −0,234 |
| TrpB | −0,026 | −0,069 |
| IGP dehydratase | +0,021 | +0,009 |
| NucB | −0,007 | +0,043 |

---

## 2. Significância, por regime

Células com p calibrado no piso (≤ 0,0099):

| Modelo | Métrica | Regime | No piso |
|---|---|---|---|
| `pairwise` | Pearson | **interpolação** | **5 / 5** |
| `pairwise` | Pearson | extrapolação | 7 / 15 |
| `pairwise` | Spearman | interpolação | **0 / 5** |
| `pairwise` | Spearman | extrapolação | 3 / 15 |
| `global_iso` | Pearson | interpolação | 4 / 5 |
| `global_iso` | Pearson | extrapolação | 7 / 15 |
| `global_iso` | Spearman | interpolação | 0 / 5 |

---

## 3. A leitura do mapa

**Carga de treino 1: nada é aprendível.** Todos os incrementos ficam em ±0,04, em
todos os conjuntos e nas duas métricas. É consistente com a subdeterminação
estrutural documentada em `RESULTADOS_FCNN.md` §6: com n/p = 0,80 por construção, não
há informação sobre interação nem sobre a não linearidade.

**Epistasia específica é detectável — só na interpolação, só em Pearson.** 5 de 5
conjuntos com incremento positivo, todas as 5 células no piso de significância.
Magnitudes de +0,023 a +0,172.

**Na extrapolação ela desaparece ou se inverte.** ParD3 −0,527 e TrpB −0,262: o
modelo de interação é muito pior que o de escala. Só `NucB` (+0,109) e `GB1` (+0,030)
ficam positivos.

**Em Spearman, nada.** Zero de 5 células no piso na interpolação, e os incrementos
são negativos em 4 dos 5 conjuntos. **O modelo de interação não melhora o
ordenamento em nenhum regime.**

### A afirmação do mapa

> Epistasia específica existe e é calibradamente detectável, mas **apenas no regime
> de interpolação e apenas na magnitude da correlação, não no ordenamento.** No
> regime de extrapolação — que é o que a engenharia de multimutantes requer — o
> modelo de interação é inconsistente e frequentemente pior que um modelo de escala
> sem nenhuma capacidade de interação.

---

## 4. Um achado que justifica o protocolo inteiro

Em `RESULTADOS_NAC.md` §3 eu afirmei que o `global_iso` é "indistinguível do nulo em
Spearman", tratando isso como manifestação universal da invariância a transformações
monotônicas. **Vale só no regime rico em dados.**

| Célula | n treino | Ganho observado | **Mediana do nulo** | Efeito |
|---|---|---|---|---|
| GB1, carga 3 | 28.186 | −0,0005 | **−0,0003** | −0,0002 |
| ParD3, carga 2 | 431 | −0,0146 | **−0,2731** | **+0,2585** |

Sob verdade aditiva com n = 431, a isotônica **destrói o ordenamento**: produz uma
escada grosseira, cria empates em massa nas 5.858 variantes de teste, e o Spearman
colapsa. Com n = 28.186 ela aproxima a identidade e não gera empates.

**A expectativa do nulo varia de −0,27 a −0,0003 conforme o n de treino.** Não é zero,
não é constante, e em nenhum dos dois casos seria adivinhável.

Isso é a justificativa empírica do capítulo para calibrar em vez de comparar contra
zero. E implica uma leitura diferente do efeito de +0,2585: ele não significa que o
modelo global melhora o ordenamento — significa que ele **preserva** o ordenamento
muito melhor do que preservaria se a paisagem fosse aditiva. É, em si, evidência de
que a estrutura monotônica é real.

---

## 5. Ressalvas

**Uma política de σ.** Todas as 15 células usam `maior_ordem`. A variante conservadora
foi medida apenas em GB1 e TrpB na carga 3 (`RESULTADOS_NAC.md` §7), onde o
deslocamento máximo foi 0,0068. **Nas cargas 1 e 2 a fração de variantes de teste em
ordens não vistas é muito maior, e a sensibilidade pode ser maior — não foi medida.**
`NAC_SIGMA=maior_sigma sbatch slurm/nac.sbatch` replica nas 15 células.

**Cinco conjuntos, não doze.** Limite de identificabilidade do modelo pareado, não
escolha nossa (`ESPECIFICACAO.md` §7.1). O mapa vale onde o pareado é estimável.

**Uma semente de particionamento por célula** (42). A variabilidade de folds foi
medida para a FCNN (`RESULTADOS_SENSIBILIDADE.md`) mas não para o NAC.

**A interpolação tem uma célula por conjunto.** Só a carga 3 produz células de
interpolação, porque a carga de teste mínima é 3. Cinco células sustentam a conclusão
mais forte do mapa.
