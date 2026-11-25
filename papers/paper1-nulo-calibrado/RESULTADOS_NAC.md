# Artigo 1 — O Nulo Aditivo Calibrado em GB1 e TrpB

Execução local, 22/11/2026. B = 30 réplicas, carga de treino 3. Código em
`src/calibrated_null.py`, resultados em `results/nac_gb1_trpb.tsv`.

`GB1` e `TrpB` foram escolhidos porque são onde o sinal sobrevive ao baseline de
escala (`RESULTADOS_EPISTASIA_GLOBAL.md` §5): a FCNN ganha +0,55 e +0,46 em Pearson
sobre o aditivo, e o modelo global recupera apenas +0,23 e +0,29. São também as duas
paisagens combinatórias quase completas em 4 posições.

---

## 1. O protocolo, e o controle que o valida

Para cada conjunto: $\beta$ e o ruído por ordem mutacional estimados **apenas no
treino**; B = 30 paisagens simuladas sob aditividade pura preservando $X$ e as
partições; o pipeline inteiro rodado em cada uma, com **$\alpha$ reselecionado por
réplica** (armadilha §3.2 da especificação).

Três modelos: `additive` (controle), `pairwise` (ridge com todas as interações
pareadas — o teste direto de epistasia **específica**) e `global_iso` (o baseline de
escala).

**O controle passou:** o ganho do aditivo sobre si mesmo é exatamente zero em todas
as réplicas, verificado por asserção.

### Os nulos são extremamente estreitos — e isso importa

| Exemplo | Mediana do nulo | p05 | p95 | Amplitude |
|---|---|---|---|---|
| GB1 `pairwise` Pearson (all) | −0,0142 | −0,0152 | −0,0133 | **0,002** |
| GB1 `global_iso` Spearman (all) | −0,0003 | −0,0004 | −0,0002 | 0,0002 |

A razão é estrutural: $X$ e os folds são fixos, só a realização do ruído muda, e os
conjuntos de teste são enormes (121 mil variantes em GB1). Correlações sobre amostras
desse tamanho têm erro padrão minúsculo.

**Consequência metodológica que precisa ser dita:** o NAC tem poder enorme, portanto
**efeitos trivialmente pequenos saem "significativos"**. Ver `TrpB` / `global_iso` /
Spearman adiante, com efeito de +0,0011 e p = 0,032. A leitura correta é pelo
tamanho do efeito, não pelo p.

### Nota sobre o p mínimo

Com B = 30, o menor p calibrado possível é 1/31 = **0,0323**. Todo valor de 0,0323
abaixo significa "o observado caiu fora de toda a distribuição nula", não "p =
0,032". Mais réplicas dariam resolução maior, mas os efeitos estão tão fora do nulo
que isso agregaria pouco.

---

## 2. Pearson: os ganhos são reais, e não são redução de variância

Efeito calibrado = ganho observado − mediana do nulo.

| Conjunto | Modelo | Regime | Observado | Nulo | **Efeito** | p |
|---|---|---|---|---|---|---|
| GB1 | `pairwise` | all | +0,2385 | −0,0142 | **+0,2526** | ≤0,032 |
| GB1 | `pairwise` | interpolação | +0,3224 | −0,0062 | **+0,3286** | ≤0,032 |
| GB1 | `pairwise` | extrapolação | +0,2346 | −0,0077 | **+0,2424** | ≤0,032 |
| GB1 | `global_iso` | all | +0,2090 | −0,0040 | **+0,2130** | ≤0,032 |
| GB1 | `global_iso` | extrapolação | +0,2094 | −0,0047 | **+0,2141** | ≤0,032 |
| TrpB | `pairwise` | interpolação | +0,2523 | −0,0047 | **+0,2570** | ≤0,032 |
| TrpB | `pairwise` | **extrapolação** | −0,0170 | −0,0053 | **−0,0118** | **1,000** |
| TrpB | `global_iso` | all | +0,2354 | −0,0040 | **+0,2394** | ≤0,032 |
| TrpB | `global_iso` | extrapolação | +0,2451 | −0,0046 | **+0,2497** | ≤0,032 |

**A expectativa do nulo é levemente NEGATIVA** (−0,004 a −0,017). Ou seja: sob
aditividade pura, um modelo com 2.850 parâmetros de interação inúteis **perde** um
pouco em Pearson, não ganha. O artefato de capacidade extra vai na direção oposta à
que se poderia temer.

Portanto os ganhos observados de 0,21 a 0,33 **não são artefato de redução de
variância nem de capacidade ajustando ruído**. São sinal.

### Mas o modelo pareado quase não supera o de escala

Este é o ponto central:

| Conjunto | Efeito `global_iso` | Efeito `pairwise` | Incremento da interação |
|---|---|---|---|
| GB1 (all) | +0,2130 | +0,2526 | **+0,040** |
| TrpB (all) | +0,2394 | +0,0618 | **−0,178** |

Em `GB1`, o modelo que **pode** representar epistasia bate o que **não pode** por
apenas **+0,04**. Em `TrpB` ele é pior. O volume do sinal em Pearson é efeito de
escala monotônica; o incremento atribuível a interação pareada genuína é pequeno em
um conjunto e negativo no outro.

### E na extrapolação o pareado colapsa

`TrpB`, extrapolação: `pairwise` tem efeito calibrado **−0,0118 com p = 1,000** —
pior que o nulo. Enquanto `global_iso` ganha +0,2497 no mesmo regime.

A estrutura de interação pareada **não generaliza para ordem alta**. Ela ajusta
dentro da distribuição (interpolação +0,2570) e falha fora. Em `GB1` ela ainda
sobrevive na extrapolação (+0,2424), mas sem superar o modelo de escala (+0,2141) de
forma relevante.

---

## 3. Spearman: ninguém melhora o ordenamento

| Conjunto | Modelo | Regime | Observado | Nulo | **Efeito** | p |
|---|---|---|---|---|---|---|
| GB1 | `pairwise` | all | −0,2369 | −0,0134 | **−0,2235** | 1,000 |
| GB1 | `pairwise` | extrapolação | −0,2415 | −0,0075 | **−0,2340** | 1,000 |
| GB1 | `global_iso` | all | −0,0005 | −0,0003 | **−0,0002** | 1,000 |
| GB1 | `global_iso` | interpolação | −0,0014 | −0,0012 | −0,0001 | 0,677 |
| GB1 | `global_iso` | extrapolação | −0,0002 | −0,0001 | −0,0001 | 0,903 |
| TrpB | `pairwise` | all | −0,0792 | −0,0187 | **−0,0604** | 1,000 |
| TrpB | `global_iso` | all | −0,0003 | −0,0015 | +0,0011 | ≤0,032 |

Dois fatos:

**O modelo pareado destrói o ordenamento muito além do nulo.** GB1: −0,22 calibrado.
Ele melhora a magnitude da correlação e piora o ranqueamento — comportamento típico
de sobreajuste que acerta a escala global e embaralha o detalhe.

**O `global_iso` é indistinguível do nulo em Spearman.** Efeito de −0,0002, p entre
0,68 e 0,90. É a invariância a transformações monotônicas confirmada
quantitativamente contra o nulo, não só por inspeção.

> ⚠️ **QUALIFICADO em 25/11/2026.** Isto vale no **regime rico em dados**, não em
> geral. O mapa de 15 células (`RESULTADOS_MAPA.md` §4) mostra que a mediana do nulo
> para o `global_iso` em Spearman vai de −0,0003 em GB1 carga 3 (n de treino 28.186)
> a **−0,2731** em ParD3 carga 2 (n de treino 431): com poucos dados a isotônica
> produz uma escada grosseira, cria empates em massa e o Spearman colapsa sob
> verdade aditiva. Eu havia tratado como invariância universal o que é um
> comportamento dependente de n. O valor de `TrpB` com p ≤ 0,032
e efeito +0,0011 é o exemplo do problema de poder descrito na §1: estatisticamente
detectável, cientificamente irrelevante.

---

## 4. O que o capítulo pode afirmar agora

Encadeando os quatro resultados:

1. **A FCNN não supera o aditivo na extrapolação** em nenhuma featurização nem carga
   de treino (`RESULTADOS_FCNN.md`).
2. **Metade da sua vantagem em Pearson na interpolação é escala**, reproduzível por
   um modelo sem capacidade de interação (`RESULTADOS_EPISTASIA_GLOBAL.md`).
3. **Os ganhos em Pearson de GB1 e TrpB são reais** — excedem o nulo aditivo com
   folga, e a expectativa do nulo é negativa, não positiva.
4. **Mas são de escala, não de interação.** O modelo pareado supera o de escala por
   +0,04 em GB1 e é pior em TrpB; e na extrapolação de TrpB ele é pior que o nulo.
   Nenhum dos dois melhora o ordenamento.

> A afirmação defensável: nas duas paisagens combinatórias mais completas do
> benchmark, **existe estrutura não aditiva forte e inequívoca, e ela é
> predominantemente epistasia global (escala) e não epistasia específica entre
> mutações.** O incremento atribuível a interação pareada é pequeno, inconsistente
> entre conjuntos, e não se transfere para ordem alta.

Isso é mais específico que a conclusão do preprint do DeWitt lab, que estabeleceu
equivalência agregada entre FCNN e aditivo. Aqui se decompõe *o que* é o sinal
não aditivo e se mostra que a parcela de interação específica, calibrada, é modesta.

---

## 5. Ressalvas

**B = 30.** O p mínimo é 0,0323. Suficiente porque os efeitos estão fora de toda a
distribuição nula, mas B = 100 no HPC daria resolução melhor e custa pouco como
array (`slurm/nac.sbatch`, `NAC_REPLICAS=100`).

**Ruído em ordens ausentes do treino.** ✅ **RESOLVIDO em 24/11/2026** — ver §7.

A ordem 4 não tem $\sigma$ estimável do treino (que vai até 3); usamos o $\sigma$ da
ordem 3. Em GB1 os sigmas decrescem com a ordem (0,093 / 0,062 / 0,050), então a
ordem 4 recebia o menor ruído disponível, e o nulo ficava mais limpo do que a
realidade provavelmente é. Era a ressalva mais relevante deste documento. A §7 mostra
que a conclusão não depende dela.

**Uma carga de treino, uma semente.** Carga 3 e semente de fold 42. A variabilidade
de folds é o experimento 4 do pacote HPC e segue pendente.

**Três conjuntos elegíveis não rodados.** `ParD3`, `IGP dehydratase` e `NucB` também
passam no critério de identificabilidade ($p$ pareado ≤ 25 mil) e não foram
calibrados. Rodá-los daria n = 5 para testar se o padrão "escala domina interação" é
geral ou específico das paisagens de 4 posições.

---

## 6. Próximos passos

1. **Experimento 4 do pacote HPC** — `val_frac` e `fold_seed`. Bloqueia a submissão.
2. **NAC nos outros três conjuntos elegíveis**, com B = 100. Barato como array.
3. **Quantificar a sensibilidade ao $\sigma$ da ordem 4** — rodar o NAC com
   $\sigma_4 = \sigma_2$ como alternativa e ver se alguma conclusão se move.
4. **Replicação em escala log.** Se parte do ganho de `global_iso` desaparecer ao
   ajustar o aditivo na escala em que aditividade é biofisicamente esperada, a
   decomposição escala-vs-interação muda de proporção.

---

## 7. Sensibilidade ao σ das ordens não vistas

Execução de 24/11/2026. `--sigma-unseen maior_sigma`, GB1 e TrpB, carga 3, B = 30.
Resultados em `results/nac_sigma_maior.tsv`.

A política padrão (`maior_ordem`) atribui à ordem 4 o σ da maior ordem do treino —
que nos conjuntos medidos é o **menor** da série. A variante conservadora
(`maior_sigma`) atribui o **maior** σ entre as ordens do treino. Em GB1 isso é
0,0926 contra 0,0502: **1,8× mais ruído** no nulo.

### O efeito calibrado praticamente não se move

| Conjunto | Modelo | Regime | Efeito (padrão) | Efeito (conservador) | Δ |
|---|---|---|---|---|---|
| GB1 | `pairwise` | all | +0,2526 | +0,2476 | −0,0050 |
| GB1 | `pairwise` | extrapolação | +0,2424 | +0,2393 | −0,0031 |
| GB1 | `global_iso` | all | +0,2130 | +0,2117 | −0,0013 |
| GB1 | `global_iso` | extrapolação | +0,2141 | +0,2122 | −0,0019 |
| TrpB | `pairwise` | all | +0,0618 | +0,0550 | −0,0068 |
| TrpB | `pairwise` | **extrapolação** | −0,0118 | −0,0141 | −0,0023 |
| TrpB | `global_iso` | all | +0,2394 | +0,2378 | −0,0016 |
| TrpB | `global_iso` | extrapolação | +0,2497 | +0,2477 | −0,0020 |

**Deslocamento máximo em 24 células: 0,0068**, sobre efeitos de 0,06 a 0,33 — cerca
de 2% em termos relativos. Todos os p calibrados permanecem no piso (≤ 0,032), e o
único que era 1,000 (TrpB `pairwise` extrapolação) continua 1,000.

As três conclusões da §2 e da §4 sobrevivem sem alteração:

| Conclusão | Padrão | Conservador |
|---|---|---|
| Incremento da interação em GB1 | +0,040 | **+0,036** |
| Incremento da interação em TrpB | −0,178 | **−0,183** |
| TrpB `pairwise` pior que o nulo na extrapolação | sim | **sim** |

O motivo da insensibilidade é estrutural: o nulo rende de −0,004 a −0,017 sob
qualquer política, enquanto o observado é +0,21 a +0,33. Mudar o ruído desloca a
mediana do nulo por milésimos; o observado está ordens de magnitude fora dela.

### Uma validação de corretude que caiu de graça

Nas oito células de **interpolação**, Δ = **exatamente 0,0000** — não
aproximadamente.

Tem de ser assim: a interpolação usa apenas variantes de teste de ordem 3, que
**têm** σ estimado do treino. A política só pode tocar ordens ausentes do treino, ou
seja a ordem 4, que é a extrapolação. Um Δ não nulo na interpolação indicaria
vazamento da política para onde ela não deveria alcançar.

Não era um teste planejado, mas é um e passou.

### O que isto fecha, e o que não

**Fecha** a ressalva da §5 sobre o σ das ordens não vistas, para GB1 e TrpB na
carga 3.

**Não fecha** a mesma questão nas outras 13 células do mapa de regimes, nem nas
cargas 1 e 2 — onde a fração de variantes de teste em ordens não vistas é maior,
porque o treino vai só até a ordem 1 ou 2. É plausível que a sensibilidade cresça
nessas cargas, e isso **não foi medido**. `NAC_SIGMA=maior_sigma sbatch
slurm/nac.sbatch` replica a análise nas 15 células.
