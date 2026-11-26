# Artigo 1 — A FCNN dentro do nulo calibrado

Execução no HPC em 26/11/2026. **12 de 12 células da carga de treino 3**, B = 30,
featurização `mut`. Resultados em `resultados_hpc/nac_fcnn/`.

> ⚠️ **Este documento revisa a conclusão central do capítulo.** A afirmação de que
> "epistasia específica é pequena e não melhora o ordenamento" era um **artefato de
> usar o ridge pareado como modelo epistático**. A FCNN, calibrada contra o mesmo
> nulo, encontra estrutura que o pareado não encontra.

---

## 1. A FCNN supera os dois outros modelos, e com folga

Efeito calibrado em Pearson, interpolação:

| Conjunto | **FCNN** | pareado | global (escala) |
|---|---|---|---|
| GB1 | **0,4661** | 0,3286 | 0,1574 |
| TrpB | **0,3961** | 0,2570 | 0,1676 |
| ParD3 | **0,3489** | 0,3114 | 0,1776 |
| cgreGFP | **0,1258** | — | 0,1072 |
| IGP dehydratase | **0,0907** | 0,0633 | 0,0405 |
| NucB | **0,0776** | 0,0624 | 0,0420 |
| AAV2 VP1 | **0,0713** | — | 0,0173 |
| demais | 0,019 – 0,065 | — | 0,022 – 0,062 |

Ordenamento consistente nos conjuntos com sinal: **FCNN > pareado > escala**.

Significância: a FCNN está no piso do p (≤ 0,0323) em **12/12 células** em Pearson e
**12/12** em Spearman na interpolação. O modelo de escala só chega ao piso em 1/12 em
Spearman; o pareado, em 1/5.

---

## 2. O achado que inverte a conclusão: a FCNN melhora o ORDENAMENTO

Spearman é invariante a transformação monotônica — ganho em Spearman **não pode** ser
escala. E o ridge pareado, onde é estimável, **destrói** o ordenamento. A FCNN não.

Ganho **observado** em Spearman (não o efeito calibrado — o ganho cru sobre o aditivo):

| Conjunto | Interpolação | Extrapolação | pareado (extrap.) |
|---|---|---|---|
| AAV2 VP1 | **+0,0855** | **+0,1639** | — |
| GB1 | **+0,0821** | **+0,0968** | **−0,2415** |
| ParD3 | **+0,0675** | −0,0008 | **−0,2833** |
| TrpB | **+0,0575** | **+0,0887** | **−0,0729** |
| NucB | **+0,0472** | +0,0483 | +0,0184 |
| Phototropin | +0,0188 | +0,0003 | — |
| cgreGFP | +0,0117 | +0,0066 | — |
| IGP dehydratase | +0,0098 | −0,0643 | −0,0586 |
| amacGFP | +0,0062 | +0,0246 | — |
| ppluGFP2 | +0,0034 | +0,0196 | — |
| scFv | −0,0049 | +0,0295 | — |
| avGFP | −0,0068 | +0,0033 | — |

**Interpolação:** positivo em 10/12, acima de 0,04 em 5/12.
**Extrapolação:** positivo em 9/12, acima de 0,04 em 4/12.

E onde o pareado é estimável, ele vai na direção **oposta**: GB1 −0,24 contra +0,10
da FCNN; ParD3 −0,28 contra −0,00; TrpB −0,07 contra +0,09.

> A FCNN captura estrutura que (a) **não é escala**, porque melhora o ordenamento, e
> (b) **não é o que um ridge pareado captura**, porque o pareado piora o ordenamento
> nos mesmos conjuntos. Provavelmente o gargalo de 100 unidades da rede regulariza
> onde os 2.926 parâmetros do pareado sobreajustam.

---

## 3. A concessão de hiperparâmetro NÃO explica o resultado — verificado

Eu havia declarado, antes de rodar, que fixar os hiperparâmetros publicados em vez de
reselecioná-los por réplica enviesaria o nulo para baixo e portanto **superestimaria**
o efeito da FCNN. Era o cenário em que um efeito grande ficaria ambíguo.

O diagnóstico resolve a ambiguidade. Mediana do ganho nulo, isto é quão mal cada
modelo vai numa paisagem puramente aditiva:

| Modelo | Pearson (média) | Faixa |
|---|---|---|
| FCNN | −0,0181 | −0,0911 a −0,0058 |
| pareado | −0,0229 | −0,0717 a −0,0047 |
| global | −0,0045 | −0,0364 a −0,0004 |

O handicap da FCNN é **da mesma ordem do do pareado** e, em termos absolutos,
minúsculo: −0,018 em média. Em GB1, o efeito de +0,4661 vem de um ganho observado de
+0,4594 menos um nulo de −0,0067 — **o nulo contribui 1,4% do efeito**. Ainda que
estivesse errado por um fator de dez, o efeito praticamente não se moveria.

**Conclusão: nos conjuntos com sinal, o resultado é dominado pelo ganho observado, não
pelo nulo. A concessão não o explica.**

### Mas há um lugar onde ela importa, e é preciso dizer

Nos conjuntos de efeito pequeno em Spearman, o nulo é uma fração grande do efeito:

| Conjunto | Ganho observado | Nulo | Efeito |
|---|---|---|---|
| amacGFP | +0,0062 | −0,0125 | +0,0187 |
| avGFP | **−0,0068** | −0,0152 | **+0,0083** |
| scFv | **−0,0049** | −0,0156 | **+0,0107** |

Em `avGFP` e `scFv` o ganho observado é **negativo** e o efeito "positivo" vem
inteiramente de o nulo ser mais negativo ainda. Chamar isso de "a FCNN melhora o
ordenamento" seria errado. **Nesses conjuntos o efeito calibrado mede o handicap, não
o sinal.**

É por isso que a tabela da §2 mostra o **ganho observado**, não o efeito calibrado.

---

## 4. O que precisa ser revisado no capítulo

| Afirmação anterior | Destino |
|---|---|
| "epistasia específica é pequena e inconsistente" | **revisada** — vale para o ridge pareado, não para a FCNN |
| "a interação não melhora o ordenamento em regime nenhum" | **revisada** — a FCNN melhora, em 10/12 na interpolação e 9/12 na extrapolação |
| "metade da vantagem da FCNN é escala" | **mantida** — o modelo de escala recupera ~50% em Pearson; mas a outra metade agora tem nome, e é interação |
| "na extrapolação ninguém supera o aditivo" | **revisada** — a FCNN supera em Pearson e em Spearman na maioria dos conjuntos |

A afirmação defensável passa a ser:

> A vantagem da FCNN sobre o nulo aditivo tem **duas componentes**, e ambas são reais.
> Cerca de metade do ganho em Pearson é **epistasia global** — escala, reproduzível
> por um modelo monotônico sem interação. A outra parte é **epistasia específica**, e
> ela se manifesta onde escala não pode: no **ordenamento**. Um ridge pareado não a
> captura — ele sobreajusta e piora o ordenamento — o que torna modelos de interação
> pareada um instrumento inadequado para medi-la.

Isso é mais forte e mais interessante que a conclusão anterior, e **contradiz a leitura
de que o desempenho do MULTI-evolve não envolve aprendizado de epistasia**. Envolve.
O que não se sustenta é atribuir a ele *todo* o desempenho: metade é escala, e a
progressão da Fig. 2E continua sendo artefato de redução de variância.

---

## 5. Ressalvas

**Só a carga de treino 3.** As cargas 1 e 2 (índices 12–35 do array) não rodaram. Na
carga 1 esperamos nada, pela subdeterminação; a carga 2 é a informativa que falta.

**Pooled contra por carga.** O NAC agrega todas as variantes de um regime numa
correlação única; a análise do experimento 1 calculava por carga de teste e tirava
média. Em GB1 as duas coincidem (+0,5730 e +0,5726, porque há só uma carga de teste de
extrapolação), mas em conjuntos com muitas cargas — `AAV2 VP1` vai até 23 — elas
divergem. Os números deste documento não são diretamente comparáveis aos de
`RESULTADOS_FCNN.md`. **Harmonizar as duas estatísticas é pendência antes de
submeter.**

**B = 30.** Piso do p em 0,0323. Suficiente dado o tamanho dos efeitos.

**Uma featurização.** `mut`. O one-hot de sequência não entrou no nulo.

**Hiperparâmetros fixos.** Verificado como não determinante nos conjuntos com sinal
(§3), mas a verificação rigorosa exigiria uma varredura reduzida dentro do laço.
