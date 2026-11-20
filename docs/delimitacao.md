# Delimitação do projeto

Versão de 2026-11-20.

## Pergunta guarda-chuva

> Em MLDE (*machine learning-guided directed evolution*) para multimutantes, quanto
> do desempenho vem de **epistasia genuinamente aprendida**, e sob que condições —
> volume de dados, representação e critério de nomeação de mutações — a modelagem
> epistática gera ganho real sobre um **nulo aditivo**?

A pergunta não é "o MULTI-evolve está errado". Essa já é a tese do preprint de
Visani, Verma & DeWitt, e seria um capítulo derivativo. A pergunta é sobre
**atribuição de desempenho em MLDE**, da qual o MULTI-evolve é o caso de teste mais
bem documentado disponível.

## Contexto: a controvérsia

Três fontes definem o terreno (detalhes e DOIs em `data/README.md`):

1. **Tran et al., *Science* 2026 — MULTI-evolve.** Ensemble de PLMs zero-shot nomeia
   singles benéficas → caracterização experimental de singles e duplos → FCNN com
   one-hot aprende epistasia → extrapola para ordem alta → MULTI-assembly constrói.
2. **Koo, Park & Kim, *Sig. Transduct. Target. Ther.* 2026, 11:340** — *research
   highlight* favorável. Lista quatro limitações: (i) dependência de achar singles
   benéficas suficientes; (ii) o espaço amostrado fica **em torno** de mutações
   benéficas, perdendo caminhos via neutras/deletérias; (iii) one-hot não carrega
   contatos nem estrutura; (iv) extrapolação degrada com distância mutacional.
3. **Visani, Verma & DeWitt, bioRxiv 2026** — crítica metodológica. Três achados:
   FCNN vs. aditivo dá **r = 1,00** nas três aplicações, em todas as ordens; a FCNN
   não bate Ridge aditivo nem um grid com zero camadas ocultas em teste held-out; e
   o padrão da Fig. 2E de Tran et al. (melhora ao treinar singles→duplos→triplos),
   apresentado como evidência de aprendizado de epistasia, **é esperado sob nulo
   aditivo** por redução de variância do erro com N maior.

Consequência direta para o escopo: a comparação óbvia — FCNN vs. XGBoost vs. modelos
lineares no benchmark MULTI-evolve — **já foi feita**, pelos autores do preprint, com
código e dados públicos. Um projeto que proponha isso nasce raspado.

## Os capítulos-artigos

### Artigo 1 — O protocolo de nulo calibrado

O preprint identificou o artefato de redução de variância, mas o diagnosticou caso a
caso. A contribuição aqui é transformá-lo em **instrumento**: para cada conjunto,
simular paisagens aditivas com N, estrutura de mutações e ruído *casados* ao real, e
derivar a faixa de desempenho esperada sob aditividade pura. Qualquer ganho reportado
passa a ser lido contra essa faixa, não contra zero.

Entrega dupla: o protocolo (software reutilizável) e sua aplicação aos 12 conjuntos
DMS combinatórios. Resultado esperado: um mapa de regimes nos eixos *N de treino* ×
*ordem mutacional* × *headroom epistático* (variância além do aditivo), mostrando
onde modelar epistasia paga.

Pré-requisito não negociável: fixar e justificar a transformação de escala por
conjunto (ver `data/README.md`, §3.4). Aditividade é esperada em escala log; comparar
em escala bruta é outra comparação.

### Artigo 2 — Representação importa?

Limitação (iii) de Koo et al. Ablação controlada: one-hot vs. descritores
físico-químicos vs. embeddings de PLM vs. contatos resíduo-resíduo, com as mesmas
partições e o nulo calibrado do Artigo 1. Pergunta estreita de propósito: alguma
representação captura epistasia que o one-hot não captura, **acima do nulo**?

XGBoost e Ridge com interações pareadas entram aqui não como "competidores da FCNN",
mas como sondas de qual classe de função é necessária. Resultado negativo honesto é
publicável — e é o desfecho mais provável.

### Artigo 3 — O viés de nomeação

Eixo biológico, e o território que o preprint não toca. Nas paisagens combinatórias
completas, simular retrospectivamente a nomeação do MULTI-evolve (top-k singles
benéficas) contra nomeações que incluam neutras e deletérias, e medir **que fração
dos melhores multimutantes é inalcançável por construção**.

O inventário confirma viabilidade com dois conjuntos quase completos em 4 posições
(`TRPB1`, 99,5%; `SPG1`/GB1, 93,4%) — permitindo enumeração exata, sem amostragem nem
modelo interposto. Complemento aproximado em ordem alta com `HIS7_YEAST` e
`PHOT_CHLRE`. Desenho: **exato em 4 posições, aproximado em ordem alta**, com a
concordância entre regimes como resultado em si.

Se a fração inalcançável for grande, é um achado sobre o desenho de campanhas de
engenharia, independente do modelo usado — um limite que nenhum ganho de arquitetura
resolve.

### Capítulo 4 — condicional

Se a colaboração de bancada se concretizar, validação prospectiva da nomeação
alternativa do Artigo 3. Se não, capítulo de síntese e perspectiva metodológica.
**A tese é desenhada para que a ausência do Capítulo 4 não a invalide.**

## Fora de escopo — explicitamente

- RAG
- Desenvolvimento de novo PLM
- Métodos de mutagênese molecular (MULTI-assembly e afins)
- Refutar epistasia em geral — o alvo é a **atribuição**, não o fenômeno. O preprint
  faz essa ressalva explicitamente e esta tese deve fazer o mesmo.
- Propor framework novo de engenharia antes de o nulo estar estabelecido

LoRA e *fine-tuning* ficam como extensão **condicional**, liberada só se o Artigo 2
mostrar que representação importa.

## Riscos

**Scooping.** O grupo do DeWitt tem código, dados e dianteira — e commitou no
`multievolve-baselines` em 2026-11-11, nove dias antes deste levantamento.
Mitigação: o Artigo 1 não repete a comparação deles, instrumentaliza o artefato que
eles só apontaram; o Artigo 3 é território não tocado. Acompanhar o repositório e a
eventual publicação revisada por pares do preprint.

**Dados para ordem alta.** Paisagens completas existem só em 4 posições. A faixa de
ordem que o MULTI-evolve realmente usa (5–9) só é acessível de forma esparsa. É uma
limitação a declarar, não a contornar.

## Decisões registradas

| Questão | Decisão |
|---|---|
| Pergunta central | Eixos A + B combinados |
| Produto | Tese por capítulos; cada capítulo um artigo publicável |
| Validação experimental | Incerta, a negociar → projeto desenhado como 100% *in silico*, com módulo experimental opcional |
| Computação | Núcleo em CPU (dados totalizam 375 MB); GPU só para embeddings do Artigo 2 |
