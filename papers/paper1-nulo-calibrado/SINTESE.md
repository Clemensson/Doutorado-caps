# Artigo 1 — Síntese

Escrito em 24/11/2026, depois de quatro experimentos. É o documento de leitura
primária do capítulo; os sete anteriores são o detalhamento.

---

## A pergunta

> **De que consiste a vantagem de um modelo flexível sobre o nulo aditivo na predição
> de multimutantes? Quanto dela é epistasia global — um efeito de escala, sem
> interação entre mutações — e quanto é epistasia específica?**

Essa não era a pergunta inicial. A original era mais vaga ("qual parte do ganho
sobrevive à correção pelo nulo") e foi reformulada no meio do caminho, por razões
registradas em `ESPECIFICACAO.md` §7.2. A reformulação veio dos dados, não do plano.

### Por que ela é a pergunta certa

Epistasia global e epistasia específica são fenômenos diferentes, e só o segundo é
interação entre mutações. A primeira é uma não linearidade monotônica na resposta —
um efeito de escala, que existe mesmo quando os efeitos mutacionais se somam
perfeitamente na escala latente.

A literatura de MLDE trata as duas como uma só coisa quando atribui desempenho a
"aprender epistasia". E há um instrumento barato para separá-las, que ninguém usou:

> **Spearman é invariante a transformações monotônicas das predições; Pearson não.**

Logo um ganho que aparece em Pearson e não em Spearman é escala. Um ganho que aparece
em Spearman não pode ser escala. O contraste entre as duas métricas, que Tran et al.
reportam em paralelo sem explorar, é um discriminante.

---

## A cadeia de resultados

### 1. O padrão apresentado como evidência de epistasia aparece sem epistasia

Um ridge aditivo — incapaz de representar qualquer interação — reproduz a progressão
da Fig. 2E de Tran et al. em **11 dos 12 conjuntos** (Spearman médio 0,266 → 0,483 →
0,556 conforme o treino vai de singles a triplos).

Confirma de forma independente o artefato de redução de variância que Visani, Verma &
DeWitt identificaram. *(`RESULTADOS_MARCO0.md`)*

### 2. Com comparação pareada, a FCNN não supera o aditivo na extrapolação

Reexecutando a rede no nosso pipeline, nos mesmos folds, em 12 conjuntos × 2
featurizações (24 tarefas, 95 min de treino no HPC):

| Regime | Δ Spearman (aditivo − FCNN) | |
|---|---|---|
| **extrapolação** | +0,0106 (`mut`) · **+0,0191 (`seq`, 10/12)** | nenhuma vantagem da rede |
| interpolação | −0,0194 / −0,0245 | vantagem pequena da rede |

Na extrapolação — o regime que o MULTI-evolve existe para servir, com combinações de
5 a 9 mutações — não há vantagem, em nenhuma featurização nem carga de treino.

A comparação contra a Tabela S4 publicada **exagerava** a vantagem da rede na
interpolação por um fator de três, e produzia significância espúria na extrapolação.
Comparar implementações diferentes não é comparação pareada. *(`RESULTADOS_FCNN.md`)*

### 3. A vantagem que existe está em Pearson, não em Spearman

| Carga de treino | Vantagem da FCNN em Spearman | Em Pearson | Excesso |
|---|---|---|---|
| 1 | −0,0379 | −0,0405 | −0,003 |
| 2 | +0,0010 | +0,0267 | +0,026 |
| 3 | +0,0120 | +0,0850 | **+0,073** |

Excesso agregado de **+0,0320**, IC95 [+0,0225, +0,0416], Wilcoxon **p = 1,07 × 10⁻⁶**
— e crescendo com o volume de treino. É a assinatura de absorção de não linearidade
de escala. *(`RESULTADOS_FCNN.md` §4)*

### 4. Metade dessa vantagem é reproduzível sem nenhuma interação

Um modelo $y \sim g(x^\top\beta)$ com $g$ monotônica, que por construção não pode
representar interação:

| Modelo | Ganho em Pearson, interpolação | |
|---|---|---|
| global (2 estágios) | **+0,0667** [+0,0289, +0,1046] | p = 0,0024, 10/12 |
| FCNN | +0,1338 [+0,0438, +0,2238] | p = 0,0015, 11/12 |

**Recupera ~50%.** E o Spearman do modelo de dois estágios não se move (−0,0023),
com coincidência de quatro casas decimais por conjunto — a invariância se manifestando
numericamente, e uma checagem de validade interna da implementação.

Na extrapolação, nada é significativo para ninguém.
*(`RESULTADOS_EPISTASIA_GLOBAL.md`)*

### 5. Calibrado contra o nulo, o sinal não aditivo é forte — e é escala

Nas duas paisagens combinatórias quase completas, com B = 30 réplicas de paisagens
simuladas sem epistasia:

| Conjunto | Efeito do modelo de escala | Efeito do pareado | Incremento da interação |
|---|---|---|---|
| GB1 | +0,2130 | +0,2526 | **+0,040** |
| TrpB | +0,2394 | +0,0618 | **−0,178** |

A expectativa do nulo é **negativa** (−0,004 a −0,017): sob aditividade pura, 2.850
parâmetros de interação inúteis fazem perder, não ganhar. Logo os efeitos de +0,21 a
+0,33 são sinal, não artefato.

Mas o modelo que **pode** representar epistasia bate o que **não pode** por apenas
+0,04 em GB1, e é pior em TrpB. E na extrapolação de TrpB o pareado fica **pior que o
nulo** (−0,0118, p = 1,000): a estrutura de interação pareada não generaliza para
ordem alta.

Em Spearman, ninguém melhora o ordenamento. *(`RESULTADOS_NAC.md`)*

---

## A afirmação do capítulo

> Existe estrutura não aditiva forte e inequívoca nas paisagens mais completas do
> benchmark. Ela é **predominantemente epistasia global — escala — e não epistasia
> específica entre mutações.** O incremento atribuível a interação pareada é pequeno,
> inconsistente entre conjuntos, e não se transfere para ordem alta.
>
> Consequentemente, **o desempenho de modelos flexíveis em MLDE não é evidência de
> aprendizado de epistasia** sem que escala e interação sejam separadas. Metade da
> evidência se dissolve contra um nulo de escala; o que sobra é modesto e local.

Isso é mais específico que o preprint do DeWitt lab, que estabeleceu equivalência
agregada entre FCNN e aditivo. Aqui se decompõe **o que** é o sinal não aditivo, e se
mostra que a parcela de interação específica, calibrada, é pequena.

### Recomendação metodológica que decorre

Três coisas, que custam pouco e que nenhum trabalho de MLDE que examinamos faz:

1. **Reportar Pearson e Spearman em paralelo e explorar o contraste.** O excesso em
   Pearson é um discriminante de escala contra interação, disponível de graça.
2. **Incluir um baseline de epistasia global** — aditivo mais transformação monotônica
   aprendida — antes de atribuir desempenho a interação.
3. **Calibrar contra um nulo aditivo casado**, não contra zero. A expectativa do nulo
   não é zero, e pode ser de qualquer sinal.

---

## Onde isto é verificável, e onde não

O limite não é computacional. Um modelo de epistasia pareada tem $p + p(p-1)/2$
parâmetros, e isso só é identificável onde $p$ é pequeno:

| Conjuntos | $p$ pareado | |
|---|---|---|
| ParD3, GB1, TrpB, IGP dehydratase, NucB | 703 – 24.531 | verificável |
| scFv, AAV2 VP1 | 95.703 – 141.778 | não |
| 4 GFPs, Phototropin | 588.070 – **2.252.503** | não |

**Epistasia pareada só é estimável nas paisagens de poucas posições** — que são as
mesmas em que a densidade de duplos medidos por par de posições é alta. Nos outros
sete conjuntos a decomposição escala-*vs*-interação é inverificável com os dados
existentes, por mais flexível que seja o modelo.

Isso delimita a afirmação do capítulo: ela vale onde foi testada, e o teste não é
possível em outro lugar.

---

## O que falta antes de submeter

| Item | Por quê bloqueia |
|---|---|
| NAC nos 5 conjuntos × 3 cargas (13 das 15 células faltam) | A afirmação da §5 repousa em 2 conjuntos e 1 carga |
| Sensibilidade a `val_split` (0,05 / 0,20) | O 10% é escolha nossa, não do artigo |
| Variabilidade de folds (4 sementes) | Uma semente não sustenta efeitos de 0,02 a 0,13 |
| Sensibilidade ao $\sigma$ da ordem 4 no nulo | Escolha declarada e não quantificada; afeta a §5 |
| Replicação em escala log | Se o aditivo for ajustado na escala biofisicamente esperada, a proporção escala/interação pode mudar |

Os quatro primeiros estão preparados como *array jobs* em `hpc_fcnn_rerun/`. O
último exige uma decisão de escala por conjunto antes de rodar.

### Ressalva honesta sobre a carga de treino 1

Em todos os conjuntos, **n_treino/p = 0,80 por construção** na carga 1: o filtro de
estringência faz $p$ = número de singles, e o treino são 4/5 deles. O sistema é
subdeterminado, o $\alpha$ colapsa no piso da grade em 8 dos 12 conjuntos, e os
valores **não são reproduzíveis entre plataformas** — divergência de até 0,14 entre o
HPC e a máquina local, contra 5 × 10⁻¹⁵ nas cargas 2 e 3. A carga 1 não deve ser
reportada com precisão decimal.

---

## Mapa dos documentos

| Documento | Conteúdo |
|---|---|
| **`SINTESE.md`** | este — leitura primária |
| `ESPECIFICACAO.md` | o método formal, as armadilhas, e a revisão de 24/11 (§7) |
| `PROTOCOLO_ALINHADO.md` | o protocolo de Tran et al. reconstruído de três fontes |
| `RESULTADOS_MARCO0.md` | resultado 1 — a progressão sem epistasia |
| `RESULTADOS_ALINHADO.md` | comparação contra a Tabela S4 publicada (superada pelo seguinte) |
| `RESULTADOS_FCNN.md` | resultados 2 e 3 — reexecução pareada e a assimetria |
| `RESULTADOS_EPISTASIA_GLOBAL.md` | resultado 4 — a metade recuperável |
| `RESULTADOS_NAC.md` | resultado 5 — a calibração em GB1 e TrpB |
