# Artigo 1 — Comparação pareada no protocolo alinhado

Execução de 2026-11-20. Protocolo documentado em `PROTOCOLO_ALINHADO.md`.

```
python -I papers/paper1-nulo-calibrado/src/aligned_protocol.py \
    --data-dir data/external/zenodo-17620759 \
    --out papers/paper1-nulo-calibrado/results/alinhado_all.tsv
python -I papers/paper1-nulo-calibrado/src/compare_to_s4.py --aligned ... --s4 ...
python -I papers/paper1-nulo-calibrado/src/analyze_deltas.py --comparison ...
```

**288 de 288 células da Tabela S4 foram pareadas** — conjunto × carga de treino ×
carga de teste. A comparação deixa de ser indicativa.

---

## 1. O quadro geral: as duas séries são quase a mesma

| | Valor |
|---|---|
| Correlação entre as séries aditivo e MULTI-evolve | **0,9804** |
| Aditivo ≥ FCNN | **155 de 288 células (53,8%)** |
| Δ médio (aditivo − FCNN), Spearman | **+0,0083** · IC95 [+0,0020, +0,0147] |

Δ positivo significa aditivo melhor. O modelo aditivo é, no agregado, **ligeiramente
superior** à FCNN — e o intervalo exclui zero, embora a magnitude seja trivial.

Por carga de treino:

| Carga de treino | Δ Spearman | Δ Pearson |
|---|---|---|
| 1 | **+0,0379** | +0,0405 |
| 2 | −0,0010 | −0,0267 |
| 3 | −0,0120 | −0,0850 |

Com apenas singles, o aditivo vence. Com duplos, é empate técnico (Δ = −0,001).
Com triplos, a FCNN tem vantagem de um centésimo em Spearman — mas de **oito
centésimos em Pearson**. Essa discrepância é o achado da §3.

---

## 2. A vantagem da FCNN está na interpolação, não na extrapolação

Separando as células pelo regime — carga de teste dentro da faixa de treino
(interpolação) ou além dela (extrapolação):

| Regime | Células | Δ Spearman médio | Aditivo ≥ FCNN | Wilcoxon |
|---|---|---|---|---|
| **Interpolação** (teste ≤ treino) | 12 | **−0,0613** | **0 de 12 (0%)** | p = 0,00049 |
| **Extrapolação** (teste > treino) | 240 | **+0,0120** | 139 de 240 (57,9%) | p = 0,0032 |

A inversão é limpa e estatisticamente sustentada em ambas as direções. E a estrutura
fica mais nítida ao medir a distância da fronteira de treino:

| Distância (teste − treino) | Células | Δ Spearman |
|---|---|---|
| 1 | 24 | −0,0172 |
| 2 | 33 | −0,0123 |
| **3** | 29 | **+0,0382** |
| **4** | 24 | **+0,0410** |
| **5** | 21 | **+0,0350** |
| 6 | 18 | +0,0305 |
| 7 | 15 | +0,0235 |
| 8 | 13 | +0,0092 |
| 9–22 | 78 | ruído em torno de zero |

A vantagem da FCNN é **local**: vale dentro da distribuição de treino e até duas
mutações além da fronteira. De três a oito mutações de distância ela se inverte, e o
aditivo passa a ser melhor. Acima disso, o sinal se dissolve em ruído.

### Por que isso importa

O propósito declarado do MULTI-evolve é extrapolar de singles e duplos para
multimutantes de ordem alta — as aplicações experimentais usam combinações de cinco a
nove mutações. **É exatamente a faixa em que o modelo aditivo é melhor.** A vantagem
da FCNN concentra-se no regime que o framework não precisa resolver, porque ali já
existem dados.

Isso é mais específico do que o achado do preprint do DeWitt lab, que mostrou
equivalência agregada. A equivalência agregada esconde uma inversão de sinal: há
estrutura local que a FCNN captura e que não generaliza para longe.

---

## 3. A vantagem da FCNN é maior em Pearson que em Spearman — e isso a identifica

Spearman é invariante a transformações monotônicas das predições; Pearson não. Uma
paisagem aditiva composta com uma não linearidade monotônica — **epistasia global**
ou não específica, que é efeito de escala e não interação entre mutações — penaliza o
modelo aditivo em Pearson e **não** em Spearman.

Portanto, se a vantagem da FCNN for sistematicamente maior em Pearson, ela é
atribuível a absorver não linearidade de escala, não a aprender epistasia específica.

| Carga de treino | Vantagem FCNN (Spearman) | Vantagem FCNN (Pearson) | Excesso em Pearson |
|---|---|---|---|
| 1 | −0,0379 | −0,0405 | −0,0026 |
| 2 | +0,0010 | +0,0267 | **+0,0257** |
| 3 | +0,0120 | +0,0850 | **+0,0731** |

Agregado sobre as 288 células:

> Excesso de vantagem em Pearson sobre Spearman: **+0,0320**
> IC95 [+0,0225, +0,0416] · positivo em 165/288 células (57,3%) · **Wilcoxon p = 1,07 × 10⁻⁶**

O excesso **cresce monotonicamente com o volume de treino**: praticamente nulo com
singles, +0,026 com duplos, +0,073 com triplos. É o que se espera se o que a rede
adquire com mais dados for principalmente o formato da curva de resposta, não a
estrutura de interação.

Por conjunto, o efeito é mais forte justamente nas paisagens pequenas de 4 posições:

| Conjunto | Excesso em Pearson |
|---|---|
| TrpB | +0,2009 |
| ParD3 | +0,1126 |
| cgreGFP | +0,0969 |
| GB1 | +0,0856 |
| ppluGFP2 | +0,0516 |
| amacGFP | +0,0479 |
| avGFP | +0,0375 |
| NucB | +0,0269 |
| AAV2 VP1 | +0,0052 |
| scFv | +0,0035 |
| Phototropin | −0,0050 |
| IGP dehydratase | −0,0095 |

### A consequência conceitual

Epistasia global e epistasia específica são coisas diferentes, e só a segunda é
interação entre mutações. O desenho de Tran et al. não as separa: reporta Pearson e
Spearman em paralelo sem explorar o contraste entre as duas. O contraste, usado como
instrumento, é informativo — e aponta que a parcela da vantagem da FCNN que não é
local é majoritariamente de escala.

Um modelo aditivo seguido de uma transformação monotônica aprendida — isto é, um
modelo de epistasia global explícito, sem nenhuma capacidade de interação — deveria
então recuperar a maior parte da vantagem em Pearson. **Esse é o experimento decisivo
e ainda não foi feito.** Entra como baseline obrigatório.

---

## 4. Tabela global (`all`), Spearman

| Conjunto | Aditivo L1/L2/L3 | MULTI-evolve L1/L2/L3 |
|---|---|---|
| AAV2 VP1 | 0,0985 / **0,7131** / 0,6541 | **0,2759** / 0,5313 / **0,7533** |
| GB1 | **0,2086** / 0,3544 / 0,4725 | 0,1229 / **0,4467** / **0,5146** |
| IGP dehydratase | 0,1381 / **0,4453** / **0,6637** | **0,1677** / 0,4282 / 0,5484 |
| NucB | **0,1967** / **0,2913** / 0,3038 | 0,0967 / 0,2733 / **0,3952** |
| ParD3 | **0,2496** / 0,4122 / 0,4143 | 0,2144 / **0,4207** / **0,4248** |
| Phototropin | −0,1124 / **0,7320** / 0,8327 | **−0,0422** / 0,7219 / **0,8492** |
| TrpB | 0,1593 / **0,2232** / 0,2330 | **0,1704** / 0,2147 / **0,2821** |
| amacGFP | **0,6586** / **0,8791** / 0,9014 | 0,5741 / 0,8625 / **0,9249** |
| avGFP | **0,5807** / **0,8340** / 0,8561 | 0,4014 / 0,7574 / **0,8636** |
| cgreGFP | **0,6717** / 0,8192 / 0,8245 | 0,5872 / **0,8210** / **0,8424** |
| ppluGFP2 | **0,7793** / **0,9142** / 0,9206 | 0,6640 / 0,8945 / **0,9410** |
| scFv | 0,4423 / 0,6892 / 0,7155 | **0,4964** / **0,6932** / **0,7792** |

---

## 5. Ressalvas, explicitamente

**5.1 Isto é "nosso aditivo contra a FCNN deles".** Os números do MULTI-evolve vêm da
Tabela S4; não reexecutamos a rede. Diferenças podem, em princípio, vir de detalhes
de implementação em vez da classe de modelo. O controle correto é reexecutar a FCNN
no nosso pipeline — o `multievolve_hyperparameter_sweep.py` do DeWitt lab fornece o
caminho. **Até isso ser feito, as conclusões das §2 e §3 são fortes mas não
definitivas.** É a pendência mais importante do capítulo.

**5.2 A interpolação tem apenas 12 células.** Carga de teste 3 com treino 3, uma por
conjunto. O resultado é unânime (12/12) e o Wilcoxon é significativo, mas a amostra
é pequena e o regime é um só.

**5.3 Composição dos folds.** A ordenação de empates pode diferir da do notebook de
referência (ver ressalva de fidelidade em `PROTOCOLO_ALINHADO.md`). Quantificável
variando `--seed`; ainda não quantificado.

**5.4 Escala.** Tudo aqui está em min-max [0,1], fiel ao artigo. A replicação em
escala log é um experimento pendente de valor próprio, e interage diretamente com a
§3: parte do excesso em Pearson pode desaparecer se o aditivo for ajustado em escala
log.

---

## 6. O que isto faz com o nulo calibrado

O capítulo agora tem alvos numéricos precisos, em vez de uma pergunta geral:

1. **Δ = +0,0120 na extrapolação** — é maior que a variabilidade de um nulo aditivo?
2. **Δ = −0,0613 na interpolação** — a vantagem local da FCNN sobrevive à calibração?
3. **Excesso de +0,0320 em Pearson** — quanto dele um modelo de epistasia global
   explícito recupera?

### Próximos passos, reordenados

1. **Reexecutar a FCNN no nosso pipeline** (ressalva 5.1). Virou prioridade sobre o
   NAC, porque todas as conclusões dependem dela.
2. **Baseline de epistasia global**: aditivo + transformação monotônica aprendida
   (regressão isotônica ou spline monotônica sobre $x^\top\beta$). Separa escala de
   interação, e é o teste direto da §3.
3. Implementar o NAC e aplicá-lo aos três alvos numéricos acima.
4. Replicação em escala log.
5. Quantificar a variabilidade de folds por semente.
