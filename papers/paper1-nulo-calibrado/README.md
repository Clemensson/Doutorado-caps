# Artigo 1 — O protocolo de nulo aditivo calibrado

**Pergunta.** Qual é a faixa de desempenho esperada sob aditividade pura, dado o N, a
estrutura de mutações e o ruído de um conjunto real — e qual parte do ganho reportado
por modelos epistáticos sobrevive a essa correção?

**Contribuição.** Visani, Verma & DeWitt identificaram que o padrão da Fig. 2E de
Tran et al. é esperado sob nulo aditivo, por redução de variância do erro com N maior,
mas o diagnosticaram caso a caso. Aqui esse artefato vira instrumento: simulação de
paisagens aditivas casadas ao conjunto real, produzindo a faixa nula de referência.

**Entregas.** (1) O protocolo, como software reutilizável. (2) Sua aplicação aos 12
conjuntos DMS, gerando um mapa de regimes em *N de treino* × *ordem mutacional* ×
*headroom epistático*.

**Pré-requisito.** Fixar e justificar a transformação de escala por conjunto
(`data/README.md`, §3.4).

Estado: não iniciado. Depende de Python 3 (`docs/ambiente.md`).
