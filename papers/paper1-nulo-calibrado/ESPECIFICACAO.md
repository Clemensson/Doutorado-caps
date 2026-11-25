# Artigo 1 — Especificação do método

Versão de 2026-11-20. Documento vivo: alterações metodológicas depois do início
das execuções devem ser registradas no histórico do git com justificativa.

---

## 1. O problema, formalizado

### 1.1 Notação

Seja $p$ o número de mutações pontuais distintas observadas em um conjunto. Cada
variante $i$ é representada por $x_i \in \{0,1\}^p$, indicando quais mutações estão
presentes. O fenótipo medido, em uma escala declarada $g(\cdot)$, é modelado como

$$y_i = \beta_0 + x_i^\top \beta + \varepsilon_i, \qquad \varepsilon_i \sim \mathcal{N}(0, \sigma^2)$$

Esse é o **modelo aditivo**. Por construção, todas as interações entre mutações são
identicamente nulas: é o nulo natural para qualquer afirmação sobre epistasia.

A ordem mutacional de uma variante é $k_i = \mathbf{1}^\top x_i$.

### 1.2 O artefato que Tran et al. interpretaram como epistasia

Tran et al. treinaram FCNNs em três subconjuntos encaixados — só singles; singles +
duplos; até triplos — e observaram que o desempenho em multimutantes separados para
teste **melhora conforme o conjunto de treino cresce**. Isso foi apresentado como
evidência de que a rede aprende epistasia (Fig. 2E).

O problema é que esse padrão tem **expectativa não nula sob aditividade pura**. Com o
estimador ridge $\hat\beta = (X^\top X + \lambda I)^{-1} X^\top y$, a variância da
predição em uma variante nova $x_\ast$ é

$$\mathrm{Var}(x_\ast^\top \hat\beta) \;=\; \sigma^2\, x_\ast^\top (X^\top X + \lambda I)^{-1} X^\top X (X^\top X + \lambda I)^{-1} x_\ast$$

que **decresce monotonicamente** conforme linhas são adicionadas a $X$. Um duplo ou um
triplo, sob aditividade, não ensina nada sobre interações: ele fornece uma medição
redundante dos mesmos coeficientes $\beta$ das singles que o compõem. Mais medições →
$\hat\beta$ melhor estimado → predição melhor em dados separados. **Zero epistasia
envolvida.**

Logo, a estatística "melhora ao enriquecer o treino" não distingue aprendizado de
epistasia de simples redução de variância. Os testes *t* emparelhados de Tran et al.
comparam essa melhora contra zero, quando o alvo correto de comparação é a melhora
que a aditividade já produz.

Visani, Verma & DeWitt identificaram esse ponto e o demonstraram ajustando um modelo
aditivo aos mesmos dados encaixados, reproduzindo o padrão. **Diagnosticaram o
artefato caso a caso.** O que falta — e é a contribuição deste capítulo — é
transformá-lo em instrumento geral.

---

## 2. O protocolo: Nulo Aditivo Calibrado (NAC)

A ideia é simular paisagens **sem nenhuma epistasia**, mas casadas ao conjunto real em
tudo o mais — mesmo desenho experimental, mesma composição de ordens, mesma razão
sinal-ruído, mesmas partições — e rodar nelas o pipeline inteiro que se quer avaliar.
A distribuição resultante da estatística de interesse é o alvo de comparação correto.

### Entradas

- Conjunto real $D = \{(x_i, y_i)\}$ com partição treino/teste fixa
- Um pipeline $P$ qualquer (FCNN, XGBoost, ridge com interações, …), tratado como caixa-preta com interface ajustar/predizer
- Uma estatística $T$ (ex.: $\Delta$ de Spearman entre dois regimes de treino encaixados)

### Passo 1 — Escala

Escolher e **declarar** $g(\cdot)$ por conjunto. Aditividade é esperada em escala
logarítmica, quando os efeitos são contribuições termodinâmicas independentes para
estabilidade ou catálise. Comparar aditivo e FCNN em escala bruta e em escala log não
é a mesma comparação. Conjuntos em brilho bruto (os três `Somermeyer_2022`, com scores
em centenas a dezenas de milhares) exigem decisão explícita e justificada.

### Passo 2 — Ajustar o gerador do nulo

**Somente na porção de treino** — ajustar no conjunto completo vazaria informação do
teste para dentro do nulo. Ajustar ridge aditivo por validação cruzada aninhada,
obtendo $\hat\beta$ e $\hat\lambda$. Estimar o ruído por uma das vias:

| Via | Modelo de ruído | Papel |
|---|---|---|
| (a) | homocedástico, $\hat\sigma^2 = \mathrm{RSS}/(n - \mathrm{df})$ | análise de sensibilidade |
| (b) | **por ordem mutacional**, $\hat\sigma^2_k$ | **padrão** |
| (c) | semiparamétrico: reamostragem de resíduos, estratificada por ordem | robustez a não normalidade |

A via (b) é padrão porque variantes de ordem alta tipicamente têm ruído maior (menos
leituras) e pior ajuste aditivo; um $\hat\sigma^2$ único tornaria o nulo
sistematicamente fácil ou difícil demais em ordens específicas — exatamente o eixo de
interesse.

### Passo 3 — Simular

Gerar $B$ réplicas, **preservando $X$ exatamente** (mesmas variantes, mesma composição
de ordens, mesma partição):

$$y_i^{(b)} = \hat\beta_0 + x_i^\top \hat\beta + \varepsilon_i^{(b)}$$

### Passo 4 — Rodar o pipeline completo em cada réplica

Calcular $T^{(b)}$. **A seleção de hiperparâmetros tem de acontecer dentro do laço**,
pela mesma rotina usada nos dados reais. Reaproveitar hiperparâmetros ajustados no real
enviesa o nulo.

### Passo 5 — Calibrar

$$p_{\text{cal}} = \frac{1 + \#\{b : T^{(b)} \ge T_{\text{obs}}\}}{B+1}, \qquad \text{efeito} = T_{\text{obs}} - \mathrm{mediana}(T^{(b)})$$

---

## 3. Armadilhas, e o que fazer com cada uma

**3.1 O gerador é ajustado a dados que contêm epistasia.** $\hat\beta$ captura a
projeção aditiva de uma paisagem possivelmente epistática, e a variância epistática
cai em $\hat\sigma^2$. O nulo fica com variância total realista e estrutura de
interação nula — que é precisamente o nulo correto para a pergunta *"aditividade
sozinha produz esse padrão?"*. Mas isso tem uma consequência que **deve ser
declarada**: o nulo tem desempenho absoluto pior que o real, porque parte do sinal
real virou ruído no nulo. Portanto **compare melhoras (diferenças), nunca níveis
absolutos.** Essa é a principal restrição interpretativa do protocolo.

**3.2 Hiperparâmetros.** Ver Passo 4. É o erro mais fácil de cometer e o que mais
infla falsos positivos.

**3.3 Partições idênticas.** Treino/teste precisa ser bit-a-bit o mesmo entre real e
simulado, para preservar os efeitos de desenho que são a fonte do artefato.

**3.4 Coeficientes não identificados.** Mutações que aparecem só em variantes de teste
não têm $\beta$ estimável. Decidir e declarar: descartar tais variantes ou encolher a
zero. A escolha afeta a comparação e precisa ser a mesma no real e no nulo.

**3.5 Dois conjuntos não sustentam o protocolo original.** `PHOT_CHLRE_Chen_2023` tem
2.122 singles e apenas **176 duplos**; `Q65J43_BACLD_g4_Thomas_2025` tem 220 singles e
850 duplos. O MULTI-evolve treina em singles + duplos. Tratar à parte ou excluir com
justificativa explícita — nunca silenciosamente.

---

## 4. Entregas

**(1) O software.** Implementação do NAC, agnóstica a pipeline. É o que torna o
capítulo reutilizável por terceiros, e é metade da contribuição.

**(2) O mapa de regimes.** Para os 12 conjuntos, o efeito calibrado em função de:

- $n_{\text{train}}$ (escala log)
- ordem máxima no treino (1, 2, 3)
- **headroom epistático** $h = R^2_{\text{CV}}(\text{pareado}) - R^2_{\text{CV}}(\text{aditivo})$

O $headroom$ é a medida de quanta epistasia *aprendível* existe no conjunto, e é o
eixo que deve prever onde modelar epistasia paga. A hipótese do capítulo é que o
efeito calibrado seja aproximadamente nulo em todo o regime de $n$ pequeno que as
campanhas reais de engenharia ocupam, e positivo só onde $h$ é alto **e** $n$ é grande
— regime que o benchmark DMS ocupa, mas as aplicações do MULTI-evolve não.

---

## 5. Marco zero: antes de qualquer FCNN

O primeiro resultado computacional não envolve rede neural nenhuma.

> **Treinar apenas ridge aditivo** em subconjuntos encaixados (singles / +duplos /
> +triplos), avaliar em multimutantes separados, e mostrar que o desempenho melhora
> com o enriquecimento do treino — na ausência total de capacidade epistática.

Se esse padrão aparecer, o artefato está demonstrado no nosso próprio pipeline, de
forma independente, e a necessidade do NAC fica estabelecida sem depender de nenhuma
afirmação sobre a FCNN.

Ordem de execução:

1. `F7YBW8_MESOW_Aakre_2015` — 9.192 variantes, 4 posições, 37 mutações. O menor
   conjunto: iteração rápida, ciclo de depuração curto.
2. `SPG1_STRSG_Wu_2016` (GB1) — 149.360 variantes, paisagem canônica da literatura.
3. `TRPB1_THEMA_Tm9D8_Johnston_2024` — 159.128 variantes, 99,5% completa.

Custo computacional: desprezível. Ridge em matriz binária esparsa com $p \le 76$ nos
três casos.

### Antes de rodar: conferir o protocolo original

Cruzar com as tabelas suplementares já obtidas, para que as partições e a composição
de treino sejam as mesmas de Tran et al. e não uma reinvenção nossa:

- `Table S3 MULTI-evolve benchmarking training composition and encodings.xlsx`
- `Table S4 MULTI-evolve benchmarking split by mutational load.xlsx`
- `Table S7 Benchmarking datasets.xlsx`

E comparar com a implementação de referência em
`data/external/multievolve-baselines/analysis/additive-proteingym_fig2ef.ipynb`, que é
exatamente a reanálise da Fig. 2E.

---

## 6. Pendências de decisão

- [x] Escala $g(\cdot)$ por conjunto — **resolvido**: min-max [0,1], ver `PROTOCOLO_ALINHADO.md`
- [x] Tratamento de coeficientes não identificados (§3.4) — **resolvido por construção** pelo filtro de estringência
- [x] $B$ (número de réplicas) — **B = 30 local, B = 100 no HPC**; ver `RESULTADOS_NAC.md` §1
- [x] Definir se o *headroom* é estimado em todos os conjuntos ou só nos ricos em dados — **resolvido pela §7 abaixo, e não como se esperava**

---

## 7. Revisão de 24/11/2026

Tudo acima é o texto original de 20/11 e **fica como registro**. Esta seção
documenta o que mudou e por quê. O plano não foi reescrito para casar com os
resultados; a divergência está registrada.

### 7.1 A entrega (2) não é alcançável como especificada

A §4 previa um mapa de regimes sobre **os 12 conjuntos**, com o *headroom*
epistático $h = R^2_{CV}(\text{pareado}) - R^2_{CV}(\text{aditivo})$ como eixo.

Um modelo pareado tem $p + p(p-1)/2$ parâmetros. Medido:

| Conjuntos | $p$ | $p$ pareado | Estimável |
|---|---|---|---|
| ParD3, GB1, TrpB, IGP dehydratase, NucB | 37–221 | 703 – 24.531 | sim |
| scFv, AAV2 VP1 | 437–532 | 95.703 – 141.778 | não |
| 4 GFPs, Phototropin | 1.084–2.122 | 588.070 – **2.252.503** | não |

Não é limite de máquina: **não existem dados que identifiquem 2,25 milhões de
parâmetros de interação** a partir de alguns milhares de variantes. A última
pendência da §6 — "em todos os conjuntos ou só nos ricos em dados" — tinha, portanto,
uma resposta imposta pelos dados, e não uma escolha nossa.

Isso é um achado e entra no artigo: **epistasia pareada só é estimável nas paisagens
de poucas posições**, que são as mesmas em que a densidade de duplos medidos por par
de posições é alta.

### 7.2 A pergunta do capítulo foi reformulada

A pergunta original — "qual parte do ganho reportado sobrevive à correção pelo nulo" —
foi respondida, mas o trabalho revelou uma pergunta mais específica e mais
informativa, que é a que os dados sustentam:

> **De que consiste a vantagem de um modelo flexível sobre o nulo aditivo? Quanto
> dela é epistasia global — um efeito de escala, sem interação entre mutações — e
> quanto é epistasia específica?**

A reformulação não foi planejada. Ela veio da assimetria Pearson/Spearman observada
na reexecução da FCNN (`RESULTADOS_FCNN.md` §4), e o baseline de epistasia global que
ela motivou **não constava desta especificação**. Registrar isso importa: foi uma
adição guiada pelos dados, não um item do plano.

### 7.3 Entregas revisadas

1. **O software do NAC**, agnóstico a pipeline — inalterado, e entregue.
2. **A decomposição escala *vs* interação**, em dois níveis de cobertura:
   - nos **12 conjuntos**, via FCNN e modelo de epistasia global (feito);
   - nos **5 conjuntos identificáveis**, o incremento de interação pareada
     calibrado contra o nulo aditivo.
3. **O limite de identificabilidade** da §7.1 como fronteira declarada do método,
   não como lacuna.

### 7.4 Estado das entregas — atualizado em 25/11/2026

As três entregas da §7.3 **estão cumpridas**.

| Item | Estado |
|---|---|
| NAC nos 5 conjuntos × 3 cargas (15 células) | ✅ `RESULTADOS_MAPA.md` |
| Sensibilidade a `val_split` (0,05 / 0,20) | ✅ `RESULTADOS_SENSIBILIDADE.md` |
| Variabilidade de folds (4 sementes) | ✅ `RESULTADOS_SENSIBILIDADE.md` |
| Sensibilidade ao $\sigma$ da ordem 4 | ⚠️ parcial — só GB1 e TrpB, carga 3 |
| Replicação em escala log | ✅ `RESULTADOS_ESCALA.md`, reformulada |
| Documento de síntese | ✅ `SINTESE.md` |

### 7.5 O que permanece aberto, e não bloqueia

Nenhum destes impede a submissão; todos limitam a generalidade de uma afirmação já
feita, e isso está declarado nos respectivos documentos.

| Aberto | Por quê importa |
|---|---|
| σ nas cargas 1 e 2 | a fração de variantes de teste em ordens não vistas é maior ali, e a sensibilidade pode crescer |
| Escala testada em 3 conjuntos, uma família de ensaio | a *forma* da não linearidade pode ser específica de fluorescência |
| A forma da não linearidade não tem nome | sabemos que não é censura e que é só 15–26% log; o resto é monotônico não identificado |
| Teste simétrico (exponenciar AAV2 VP1 e scFv) | confirmaria a direção do efeito de escala |
| Variabilidade de folds do NAC | medida para a FCNN, não para o NAC |
| A interpolação tem 5 células | só a carga 3 produz células de interpolação |
