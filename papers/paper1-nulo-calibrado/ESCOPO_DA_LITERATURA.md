# O que os artigos base realmente afirmam, e sobre quais dados

Verificação feita em 26/11/2026 nos dois PDFs de `literature/`, por busca textual.
Motivada por uma pergunta de contexto do orientando, e ela expôs **dois erros de
enquadramento do capítulo**.

> ⚠️ **Limite desta verificação: Tran et al. (Science 2026) continua ausente.** Tudo
> que o projeto afirma sobre o que o artigo original diz vem (a) das citações diretas
> no preprint do DeWitt lab, (b) do resumo de Koo et al., e (c) das tabelas
> suplementares. Está pendente desde 20/11 (`data/README.md` §4). Parte do que segue
> só foi notado agora **porque** nunca lemos a fonte primária.

---

## 1. "Mutações compensatórias" não é afirmação de nenhum dos dois artigos

Busca textual: **`compensat*` aparece ZERO vezes** nos dois PDFs.

O vocabulário usado é outro:

| Termo | DeWitt | Koo | Significado |
|---|---|---|---|
| `synergistic` | 9 | 2 | combinação melhor que a soma aditiva — **epistasia positiva** |
| `antagonistic` | 1 | 1 | ver abaixo |
| `epistatic interactions` | 12 | 5 | genérico |
| `neutral` / `deleterious` | 0 | 2 / 1 | ver abaixo |

**`antagonistic` não é compensatório.** Em Koo aparece só para o HuABC2: *"accounting
for antagonistic mutational interactions"* no contexto do compromisso entre expressão
e afinidade — uma mutação que ajuda uma propriedade e prejudica a outra. É
otimização multiobjetivo numa fronteira de Pareto, não resgate de uma mutação
deletéria por outra.

**O mais próximo de compensatório aparece como LIMITAÇÃO, não como resultado.** Koo,
na lista de limitações: *"optimized variants arise from combinations of mutations that
are neutral or deleterious alone. Future iterations could incorporate such mutations
to expand the sequence space"*. Ou seja: é o que o framework **não faz**, e uma
sugestão para versões futuras — exatamente o que delimitamos como Eixo B e Artigo 3.

> Portanto: o benchmark **não** foi usado para validar captura de mutações
> compensatórias. Foi usado para validar **extrapolação de singles e duplos para
> ordem alta** — Koo: *"supported extrapolation from single- and double-mutant data to
> higher-order combinations, including variants with up to 12 mutations in benchmarking
> analyses"*.

---

## 2. O erro mais grave: o escopo das afirmações do DeWitt

As três afirmações do preprint têm **escopos diferentes**, e eu as tratei como se
fossem todas sobre os mesmos dados.

| Afirmação | Escopo real |
|---|---|
| "almost perfectly correlated with an additive model's" (r = 1,00) | **as três aplicações de engenharia** — APEX, dCasRx, HuABC2 — no espaço combinatório |
| "do not outperform an additive model on held-out test data" | *"from the **original single+double training sets**"*, e a varredura refeita usou *"the published **APEX, dCasRx, and HuABC2** training data"* |
| "the same pattern is expected under a null additive model" | **o benchmark DMS**, e especificamente sobre a *inferência* da Fig. 2E |

### A consequência

> **O DeWitt lab nunca afirmou que a FCNN deixa de superar o aditivo no benchmark
> DMS.** No benchmark, a afirmação deles é mais estreita: a *progressão* da Fig. 2E
> não é evidência de aprendizado de epistasia, porque é esperada sob aditividade por
> redução de variância.

O Artigo 1 trabalhou **exclusivamente no benchmark DMS**. Logo:

1. **Nosso Marco Zero confirma o DeWitt** — é o único resultado nosso sobre os mesmos
   dados e a mesma afirmação, e reproduz a progressão com um aditivo em 11/12
   conjuntos. ✅
2. **Nosso resultado da FCNN no nulo NÃO contradiz o DeWitt.** Em
   `RESULTADOS_NAC_FCNN.md` §4 escrevi que ele *"contradiz a leitura de que o
   desempenho do MULTI-evolve não envolve aprendizado de epistasia"*. **Impreciso** —
   essa leitura, no preprint, é sobre as aplicações de engenharia, não sobre o
   benchmark.
3. **A afirmação mais forte do DeWitt nunca foi testada por nós.** O r = 1,00 nas três
   aplicações de engenharia é o resultado central deles, e não tocamos nisso.

---

## 3. A limitação do Artigo 1 que eu nunca declarei

O preprint levanta uma objeção que **se aplica igualmente a nós**:

> *"we question the relevance of this benchmarking procedure, which trains MULTI-evolve
> FCNNs on DMS datasets with tens to hundreds of thousands of variants, when the
> eventual MULTI-evolve engineering tasks train on only hundreds of variants — a
> profoundly reduced sampling regime."*

Nossos conjuntos de treino vão de 30 (ParD3, carga 1) a 28.186 (GB1, carga 3). O
regime das aplicações reais é de **centenas**. Então a conclusão do Artigo 1 —
epistasia específica detectável na interpolação — vale no regime do benchmark, e **a
transferência para o regime de engenharia não está demonstrada**.

Isso precisa entrar como limitação explícita do artigo. Não invalida nada; delimita.

E dá uma leitura nova ao nosso próprio mapa: na **carga de treino 1**, onde n é
menor e mais próximo do regime real, **nada é aprendível** (|incremento| ≤ 0,04 em
todos os conjuntos, `RESULTADOS_MAPA.md` §3). Isso é consistente com a objeção do
DeWitt, e é um argumento que ainda não exploramos.

---

## 4. A oportunidade que isto abre

As três aplicações de engenharia são onde vive a afirmação mais forte do preprint — e
**temos os dados**: `Table S14 APEX variants.xlsx`, `Table S15 dCasRx variants.xlsx`,
`Table S16 HuABC2 variants.xlsx`, já em `data/external/zenodo-18240028/`.

Aplicar o nulo calibrado ali testaria a afirmação central do DeWitt lab no terreno
dela, com um instrumento que eles não usaram. É o experimento de maior valor
marginal que resta no Artigo 1 — mais que as cargas 1 e 2 do experimento 5.

Ressalva: são conjuntos pequenos (centenas de variantes) e multiobjetivo no caso do
HuABC2, portanto o protocolo precisa de adaptação, não de reuso direto.

---

## 5. Correções a aplicar

- [x] `RESULTADOS_NAC_FCNN.md` §4 — retirar "contradiz a leitura de que o desempenho
      do MULTI-evolve não envolve aprendizado de epistasia"
- [x] `SINTESE.md` — acrescentar a limitação de regime da §3
- [ ] **Obter Tran et al.** — a pendência que gerou tudo isto
- [ ] Decidir se o nulo calibrado vai para as aplicações de engenharia (§4)
