# Epistasia em MLDE: atribuição de desempenho e viés de nomeação

**Pergunta guarda-chuva.** Em MLDE para multimutantes, quanto do desempenho vem de
epistasia genuinamente aprendida, e sob que condições — volume de dados, representação
e critério de nomeação — a modelagem epistática gera ganho real sobre um nulo aditivo?

Ver [`docs/delimitacao.md`](docs/delimitacao.md) para o escopo completo, os três
artigos planejados, o que ficou explicitamente fora e os riscos.

## Estrutura

| Diretório | Conteúdo |
|---|---|
| `docs/` | Delimitação, notas de ambiente, documentos de qualificação |
| `literature/` | PDFs das fontes primárias |
| `data/` | Catálogo de dados ([`data/README.md`](data/README.md)); dados brutos em `data/external/`, não versionados |
| `scripts/` | Scripts de propósito geral (catalogação, obtenção de dados) |
| `papers/paper1-nulo-calibrado/` | **Artigo 1** — protocolo de nulo aditivo calibrado |
| `papers/paper2-representacao/` | **Artigo 2** — ablação de representações |
| `papers/paper3-vies-nomeacao/` | **Artigo 3** — viés de nomeação de mutações benéficas |
| `papers/chapter4-condicional/` | **Capítulo 4** — validação prospectiva ou síntese |

Cada diretório de artigo segue o mesmo padrão: `src/`, `notebooks/`, `results/`,
`figures/`. Resultados e figuras geradas não são versionados — só o código que as
produz.

## Regras metodológicas do projeto

Três, e valem em todos os capítulos:

1. **Nulo aditivo em toda comparação.** Nenhum ganho é reportado contra zero.
2. **Separação por ordem mutacional.** Métricas agregadas sobre ordens misturadas
   escondem exatamente o efeito de interesse.
3. **Escala declarada e justificada.** Aditividade é esperada em escala logarítmica;
   a transformação por conjunto é decisão metodológica, não pré-processamento.

## Estado

- [x] Delimitação do escopo
- [x] Obtenção e catalogação dos dados externos (28 arquivos, 4 fontes)
- [ ] Python 3 no ambiente — ver [`docs/ambiente.md`](docs/ambiente.md)
- [ ] Reprodução independente do preprint do DeWitt lab
- [ ] Especificação de métricas e do nulo calibrado (Artigo 1)
