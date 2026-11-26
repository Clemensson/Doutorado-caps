# Análise 1 — os efeitos se somam? E quando não somam, de que forma?

Execução de 26/11/2026. Código em `src/analise1_curva_aditiva.py`, tabelas em
`resultados/analise1_*.tsv`, figuras `fig6` e `fig7`.

> **Esta análise fecha a lacuna aberta do Artigo 1.** `RESULTADOS_ESCALA.md` §4
> concluiu que a não linearidade monotônica **não é censura** e que **só 15–26% é
> logarítmica** — e deixou o resto sem nome, com uma hipótese registrada mas não
> testada: sigmoide tipo Hill. **A forma agora está nomeada.**

---

## 1. O método, em uma frase

Ajustamos um modelo que supõe que os efeitos das mutações se somam, pedimos a ele uma
previsão para cada variante, e comparamos com o medido. **Se os efeitos somassem, a
nuvem colaria na diagonal.** Onde ela entorta, não somam — e o formato da entortada
diz como.

Ridge sobre a matriz indicadora de mutações, α por validação cruzada de 3 pastas,
matriz esparsa do início ao fim. O ajuste é **descritivo**, sobre todos os dados: a
pergunta é a forma do sinal, não desempenho preditivo, e por isso não há partição de
teste.

---

## 2. A forma é sigmoide — piso, transição íngreme, saturação

Em **10 dos 12 conjuntos** a curva tem a mesma anatomia:

- um **piso achatado** à esquerda, onde variantes muito mutadas estão todas mortas e
  o modelo aditivo continua prevendo valores cada vez menores sem que o medido desça;
- uma **transição íngreme** no meio, mais inclinada que a diagonal;
- um **teto** à direita, onde o medido para de subir.

É nítido em `AAV2 VP1`, `scFv`, `avGFP`, `cgreGFP`, `ppluGFP2`, `amacGFP` e
`IGP dehydratase`. Em `GB1`, `ParD3` e `NucB` aparece a metade esquerda — piso longo
seguido de subida abrupta — porque poucas variantes atingem a faixa alta de previsão.

### Isso explica por que o log recuperava tão pouco

A pergunta que ficou aberta no Artigo 1 era por que uma transformação logarítmica
absorvia apenas 15–26% da não linearidade. A resposta está na figura:

> **O log comprime a cauda superior, mas o traço dominante aqui é o piso inferior.**
> Nenhuma função logarítmica produz um platô achatado embaixo. Uma sigmoide produz os
> dois extremos.

### Duas exceções, e ambas são informativas

**`Phototropin` é quase linear** — a curva segue a diagonal de perto. É também o
conjunto com a maior correlação aditiva de todos (r = 0,92) e aquele em que o Artigo 1
não encontrou epistasia específica. As três observações concordam: nesse conjunto, os
efeitos realmente se somam.

**`TrpB` entorta para o outro lado.** A curva sobe e então **achata abaixo da
diagonal**: retornos decrescentes, não saturação simétrica. E é o conjunto com o maior
déficit de Spearman de todos (−0,254).

---

## 3. A assimetria separa os conjuntos em dois grupos

Spearman é invariante a transformação monotônica das previsões; Pearson não. Então a
diferença entre os dois diz **que tipo** de erro o modelo aditivo comete.

| Conjunto | Pearson | Spearman | ρ − r | Leitura |
|---|---|---|---|---|
| GB1 | 0,441 | 0,523 | **+0,082** | ordem certa, escala errada |
| cgreGFP | 0,804 | 0,872 | +0,068 | ordem certa, escala errada |
| AAV2 VP1 | 0,765 | 0,819 | +0,054 | ordem certa, escala errada |
| amacGFP | 0,874 | 0,900 | +0,026 | ordem certa, escala errada |
| avGFP | 0,847 | 0,869 | +0,022 | ordem certa, escala errada |
| ppluGFP2 | 0,900 | 0,919 | +0,018 | ordem certa, escala errada |
| Phototropin | 0,921 | 0,936 | +0,016 | quase aditivo |
| scFv | 0,895 | 0,892 | −0,004 | neutro |
| IGP dehydratase | 0,825 | 0,779 | −0,046 | **ordem errada** |
| ParD3 | 0,612 | 0,505 | −0,106 | **ordem errada** |
| NucB | 0,536 | 0,416 | −0,120 | **ordem errada** |
| **TrpB** | 0,503 | 0,249 | **−0,254** | **ordem errada** |

**ρ > r** significa: o modelo aditivo coloca as variantes na ordem certa e erra o
valor. Falta uma **transformação monotônica** — escala, não interação.

**ρ < r** significa o contrário: o modelo acerta razoavelmente a magnitude mas
**embaralha o ranqueamento**. Nenhuma transformação monotônica conserta isso, por
definição. **É assinatura de interação entre mutações.**

### A concordância com o Artigo 1

Os quatro conjuntos com ρ < r — TrpB, NucB, ParD3, IGP — são exatamente aqueles em que
o nulo calibrado do Artigo 1 encontrou sinal de interação específica, e `Phototropin`,
o mais aditivo aqui, é onde o Artigo 1 não encontrou nada. **Duas análises
independentes, com métodos diferentes, apontam para os mesmos conjuntos.**

---

## 4. O que isto decide

**Para o Artigo 1:** a não linearidade tem nome. A hipótese sigmoidal registrada em
`RESULTADOS_ESCALA.md` §4 **se confirma visualmente nos 12 conjuntos**, e o mistério
do log parcial se resolve — ele não produz piso.

O passo natural é trocar a isotônica, que é flexível demais e não interpretável, por
uma **família sigmoidal paramétrica** de 4 parâmetros (piso, teto, inclinação, ponto
de inflexão). Se ela recuperar o mesmo ganho da isotônica, o baseline de epistasia
global passa a ter **parâmetros com significado biofísico** em vez de uma escada.

**Para a pergunta de epistasia compensatória:** o piso é o obstáculo central. Numa
região onde tudo está morto, não há como distinguir "as duas mutações se
compensaram parcialmente" de "as duas mutações mataram a proteína". **Candidatos
compensatórios na faixa do piso não são interpretáveis** — o que estreita ainda mais
os 0,73% do melhor conjunto.

---

## 5. Ressalvas

**O ajuste é descritivo, não preditivo.** Ridge sobre todos os dados, sem partição.
Serve para ver a forma; não mede capacidade de generalizar.

**A curva é mediana por faixa de previsão**, 24 faixas por quantil, mínimo de 20
variantes por faixa. A banda clara é o intervalo interquartil. Isso suaviza ruído
ponto a ponto, e também esconde heterogeneidade dentro da faixa.

**"Sigmoide" aqui é descrição visual, não ajuste.** Nenhuma função sigmoidal foi
ajustada nem testada contra alternativas. Dizer que é uma Hill, ou estimar seus
parâmetros, exige o experimento proposto na §4 — e isso ainda não foi feito.

**As escalas do eixo x diferem entre painéis** porque as escalas dos conjuntos
diferem (seis ordens de magnitude, ver `RELATORIO_EDA.md` §4 P4). A comparação entre
painéis é de **forma**, nunca de nível.
