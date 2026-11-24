# Artigo 1 — A FCNN reexecutada no nosso pipeline

Execução no HPC em 22/11/2026, com o pacote `hpc_fcnn_rerun/`. Resultados brutos em
`fcnn_resultados/`. Verificação independente por
`src/verify_hpc_results.py`.

**Isto resolve a ressalva 5.1 de `RESULTADOS_ALINHADO.md`.** Até aqui comparávamos o
*nosso* ridge aditivo contra a *FCNN publicada*, o que deixava aberta a possibilidade
de as diferenças vierem de detalhes de implementação em vez da classe de modelo.
Agora os dois modelos rodam no mesmo processo, nos mesmos folds, sobre os mesmos
dados.

---

## 1. Execução e custo

24/24 tarefas concluíram (12 conjuntos × 2 featurizações), todas com marcador `.ok`.

| | Valor |
|---|---|
| Tempo de treino somado | **132 min** |
| Pior tarefa isolada | **23,8 min** (GB1, one-hot de sequência) |
| Épocas efetivas | mediana **56**, faixa 16–219 (teto era 300) |

Eu havia estimado 1–5 h para a pior tarefa. O real foi 23 min — **errei por um fator
de 3 a 13**. A causa: superestimei as épocas efetivas. O *early stopping* cortou de
300 para 56 na mediana, bem mais do que eu assumi.

### Verificação de integridade

A recomputação independente confere com a análise feita no cluster **até a quarta casa
decimal**. Encontrei um problema de contagem no `analise_por_conjunto.txt`: as linhas
do aditivo aparecem duas vezes no `merged.tsv` (uma por tarefa de featurização, já
que o aditivo roda em ambas) e não foram desduplicadas, o que reportou 594 células de
extrapolação onde há 297. As cópias são **idênticas** — desvio máximo exatamente zero
— e a agregação por conjunto veio antes dos testes, então **as médias e os p-valores
não foram afetados**. O erro inflava apenas `n`.

---

## 2. Unidade de análise: o conjunto

Células dentro de um mesmo conjunto compartilham folds, dados e coeficientes; não são
independentes. Agregamos por conjunto antes de testar, portanto **n = 12** em tudo o
que segue. Delta positivo favorece o aditivo.

Essa escolha é mais conservadora que a do `merge.py`, que testava no nível de célula
(345 por featurização) e assim superestimava os graus de liberdade.

---

## 3. O resultado central: nenhuma vantagem da FCNN onde importa

### Spearman, por regime

| Featurização | Regime | Δ | IC95 | Aditivo melhor | Wilcoxon |
|---|---|---|---|---|---|
| `mut` | extrapolação | +0,0106 | [−0,0080, +0,0291] | 8/12 | p = 0,339 |
| `mut` | interpolação | −0,0194 | [−0,0464, +0,0076] | 2/12 | p = 0,077 |
| `seq` | **extrapolação** | **+0,0191** | **[−0,0006, +0,0389]** | **10/12** | p = 0,077 |
| `seq` | interpolação | −0,0245 | [−0,0476, −0,0013] | 1/12 | p = 0,021 |

**Na extrapolação — o regime que o framework existe para servir — não há vantagem da
FCNN.** Com a featurização fiel ao artigo (`seq`), o aditivo é *melhor* em 10 de 12
conjuntos, com o intervalo tangenciando zero.

A vantagem da FCNN sobrevive apenas na **interpolação**, e é pequena em Spearman
(−0,019 a −0,025).

### Comparação com o que a Table S4 sugeria

| | Contra Table S4 | Pareado no mesmo pipeline |
|---|---|---|
| Δ Spearman, interpolação | −0,0613 | **−0,0194 / −0,0245** |
| Δ Spearman, extrapolação | +0,0120 (p = 0,003) | **+0,0106 / +0,0191 (p = 0,08–0,34)** |
| Δ global | +0,0083, IC excluindo zero | **+0,0070 / +0,0143, IC incluindo zero** |

A comparação contra a tabela publicada **exagerava** a vantagem da FCNN na
interpolação por um fator de três, e sua significância na extrapolação era artefato de
comparar implementações diferentes. Esse era exatamente o risco que a ressalva 5.1
registrava — e ele se materializou.

### Por carga de treino

| Featurização | Carga 1 | Carga 2 | Carga 3 |
|---|---|---|---|
| `mut` | **+0,1375** [+0,0618, +0,2132] · 10/12 | +0,0145 [−0,0226, +0,0516] · 6/12 | −0,0247 [−0,0635, +0,0141] · 3/12 |
| `seq` | **+0,0917** [+0,0456, +0,1378] · 11/12 | **+0,0531** [+0,0017, +0,1044] · 11/12 | −0,0092 [−0,0341, +0,0156] · 3/12 |

O aditivo é **significativamente melhor** com poucos dados, e a FCNN só alcança o
empate na carga 3. Em nenhuma carga a FCNN é significativamente melhor.

Spearman global (células `all`):

| Modelo | Carga 1 | Carga 2 | Carga 3 |
|---|---|---|---|
| Ridge aditivo | 0,3376 | 0,6090 | 0,6494 |
| FCNN `mut` | 0,2001 | 0,5944 | 0,6740 |
| FCNN `seq` | 0,2459 | 0,5559 | 0,6586 |

---

## 4. O mecanismo identificado: a FCNN aprende escala, não interação

Spearman é invariante a transformações monotônicas das predições; Pearson não. Logo
**epistasia global** — não linearidade de escala, não interação entre mutações —
penaliza o aditivo em Pearson e não em Spearman. Se a vantagem da FCNN for
sistematicamente maior em Pearson, ela é atribuível a absorver escala.

### Pearson, por regime

| Featurização | Regime | Δ Pearson | IC95 | Wilcoxon |
|---|---|---|---|---|
| `mut` | extrapolação | −0,0448 | [−0,0907, +0,0012] | p = 0,151 |
| `mut` | **interpolação** | **−0,1338** | **[−0,2238, −0,0438]** | **p = 0,0015** |
| `seq` | extrapolação | −0,0155 | [−0,0567, +0,0257] | p = 0,470 |
| `seq` | **interpolação** | **−0,1304** | **[−0,2096, −0,0512]** | **p = 0,0010** |

### O excesso de vantagem em Pearson sobre Spearman

| Featurização | Regime | Excesso | IC95 | Positivo em | Wilcoxon |
|---|---|---|---|---|---|
| `mut` | extrapolação | +0,0553 | [+0,0117, +0,0990] | 9/12 | **p = 0,021** |
| `mut` | interpolação | **+0,1144** | [+0,0378, +0,1910] | **11/12** | **p = 0,0024** |
| `seq` | extrapolação | +0,0346 | [−0,0006, +0,0698] | 7/12 | p = 0,129 |
| `seq` | interpolação | **+0,1059** | [+0,0385, +0,1734] | **11/12** | **p = 0,0024** |

Significativo em três dos quatro regimes, e consistente na direção em todos. Na
interpolação, a vantagem da FCNN é de **0,13 em Pearson contra 0,02 em Spearman** —
uma diferença de seis vezes.

**Essa é a leitura do capítulo.** O que a FCNN adquire sobre o modelo aditivo é
majoritariamente o *formato da curva de resposta*, não a *estrutura de interação entre
mutações*. É uma afirmação mais específica que a do preprint do DeWitt lab, que
mostrou equivalência agregada: aqui se diz **o que** a rede está de fato aprendendo.

E torna o experimento decisivo óbvio: **aditivo + transformação monotônica aprendida**
(isotônica ou spline monotônica sobre $x^\top\beta$) — um modelo de epistasia global
explícito, sem nenhuma capacidade de interação. Se ele recuperar a maior parte dos
0,13 em Pearson, a atribuição a "aprender epistasia" fica insustentável.

---

## 5. O eixo de representação é plano — e isso confirma a reorientação do Artigo 2

A FCNN com one-hot de sequência (22 × L features, fiel ao artigo) é **pior** que a
FCNN com indicador de mutação nas cargas 2 e 3 (0,5559 vs 0,5944; 0,6586 vs 0,6740),
e melhor apenas na carga 1. Multiplicar a dimensão de entrada por até 29 vezes
(AAV2: 16.170 contra 532 features) não ajuda.

Isso converge com o achado da Tabela S3, em que o one-hot venceu os sete *encodings*
testados, incluindo PLMs de 15 bilhões de parâmetros. **Confirma a reorientação
proposta para o Artigo 2:** o eixo de representação é plano, e essa planura é
evidência de que o modelo não extrai estrutura de interação de nenhuma representação.

---

## 6. Um achado novo: a carga 1 é estruturalmente subdeterminada

As cargas 2 e 3 do aditivo batem **exatamente** com a rodada local de 20/11 (desvio
< 10⁻⁶). A carga 1 **difere em todos os 12 conjuntos**, até 0,058 em Phototropin.

A causa não é o fold — se fosse, as cargas 2 e 3 também difeririam. É esta:

> Na carga 1, **n_treino / p = 0,80 em todos os 12 conjuntos**, sempre.

E isso é estrutural, não coincidência. Após o filtro de estringência `'singles'`, toda
mutação do conjunto aparece como single medido, logo *p* = número de singles. O treino
na carga 1 são 4/5 dos singles. Portanto n/p = 0,8 **por construção**.

Consequências:

1. O sistema é **subdeterminado**: 20% dos coeficientes nunca são observados no treino
   (estão no fold retido) e ficam não identificados.
2. A matriz de desenho na carga 1 é um subconjunto da identidade — cada single
   observa exatamente um coeficiente, sem nenhuma restrição cruzada.
3. A seleção de α por GCV **colapsa no piso da grade** (0,001) em 8 dos 12 conjuntos.
   Perto de α = 0, a solução é a de norma mínima via pseudoinversa, sensível a
   detalhes numéricos: versão do BLAS, ordem de acumulação, versões de biblioteca.

Daí a divergência HPC vs local na carga 1, e só nela. A média geral quase não se move
(0,3376 vs 0,3393), e a conclusão da carga 1 — aditivo muito melhor, +0,14 — é robusta.
Mas **os valores por conjunto na carga 1 não são reproduzíveis entre plataformas e não
devem ser reportados com quatro casas decimais.**

### Isso resolve a anomalia de Phototropin

Em `RESULTADOS_MARCO0.md` eu havia sinalizado como "implausível" o salto de
Phototropin de −0,08 para 0,74 entre as cargas 1 e 2, com apenas 176 duplos
disponíveis. A explicação agora é limpa: Phototropin tem n/p = 0,80 na carga 1, **0,87
na carga 2 e 1,24 na carga 3** — é o único conjunto que permanece quase
subdeterminado em todas as cargas. Os 176 duplos não adicionam muitos *dados*, mas
adicionam **identificabilidade**: cada duplo impõe uma restrição que liga dois
coeficientes. É exatamente o que conserta um sistema subdeterminado.

Não era anomalia. Era um conjunto operando no limite da identificabilidade, e o salto
mede a transição de subdeterminado para determinado. Vale como exemplo didático no
artigo.

---

## 7. Estado do capítulo

### Resolvido

- **Ressalva 5.1** — a FCNN rodou no nosso pipeline. A comparação é pareada.
- **A direção do resultado** — nenhuma vantagem da FCNN na extrapolação, em nenhuma
  featurização, em nenhuma carga de treino.
- **O mecanismo** — a vantagem que existe é de escala (Pearson, interpolação), não de
  interação.
- **A anomalia de Phototropin** — subdeterminação, não artefato.
- **Escala de y** — min-max [0,1], documentado em `PROTOCOLO_ALINHADO.md`.

### Ressalvas que permanecem

**`val_split` não documentado.** O *early stopping* precisa de validação, e o valor
usado por Tran et al. não está em nenhuma das três fontes. Usamos 10% estratificado
por carga. A sensibilidade a isso **ainda não foi medida** — rodar com 0,05 e 0,20 é
barato nos conjuntos pequenos e deve entrar antes da submissão.

**Variabilidade de folds.** Uma semente só (42). Não quantificada.

**Interpolação tem 12 células.** Uma por conjunto (carga de teste 3 com treino 3). O
resultado é consistente (11/12 em Pearson) mas o regime é um só.

### Próximos passos, em ordem

1. **Baseline de epistasia global** — aditivo + transformação monotônica aprendida.
   Passou a ser o experimento decisivo do capítulo, porque é o teste direto da §4.
2. **Nulo Aditivo Calibrado** (Passos 2–5 da especificação), agora com alvos
   numéricos precisos: os 0,13 de Pearson na interpolação e os ~0,02 de Spearman.
3. Sensibilidade a `val_split` e a sementes de fold.
4. Replicação em escala log (interage com a §4: parte do excesso em Pearson pode
   desaparecer se o aditivo for ajustado na escala certa).
