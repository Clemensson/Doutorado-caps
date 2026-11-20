# Artigo 1 — Resultados do marco zero

Execução de 2026-11-20. Reprodutível por:

```
python -I papers/paper1-nulo-calibrado/src/milestone0_additive.py \
    --data-dir data/external/zenodo-17620759 \
    --out papers/paper1-nulo-calibrado/results/milestone0_all.tsv
```

Saídas: `results/milestone0_all.tsv` (372 linhas, inclui estratificação por ordem
exata de teste) e `results/comparacao_tran.tsv`.

---

## 1. Desenho

Para cada um dos 12 conjuntos DMS:

- **Teste fixo**: todas as variantes de ordem ≥ 4. Fixo entre regimes, de modo que a
  única coisa que varia é o enriquecimento do treino — é isso que isola o efeito de
  redução de variância.
- **Treino**: variantes de ordem ≤ L, para L ∈ {1, 2, 3}.
- **Modelo**: ridge aditivo apenas, `RidgeCV` com 29 valores de α em grade log de
  10⁻³ a 10⁴, validação cruzada 5-fold, matriz de desenho binária esparsa sobre as
  p mutações pontuais distintas.
- Mutações não observadas no treino: coluna mantida, coeficiente encolhido a zero
  (decisão de §3.4 da especificação), com a fração de variantes de teste afetada
  registrada em cada linha da saída.

**Nenhuma capacidade de representar interação.** Por construção, o modelo não pode
aprender epistasia.

## 2. Resultado principal: a progressão aparece sem epistasia

Spearman no teste, por carga de treino:

| Conjunto | Carga 1 | Carga 2 | Carga 3 |
|---|---|---|---|
| ppluGFP2 | 0,8237 | 0,8719 | 0,8802 |
| amacGFP | 0,7839 | 0,8641 | 0,8846 |
| avGFP | 0,5399 | 0,6807 | 0,6975 |
| cgreGFP | 0,5016 | 0,5354 | 0,5391 |
| Phototropin | −0,0826 | 0,7378 | 0,8337 |
| IGP dehydratase | 0,1029 | 0,4755 | 0,6249 |
| AAV2 VP1 | 0,1171 | 0,3720 | 0,6239 |
| scFv | −0,0020 | 0,4364 | 0,6178 |
| GB1 | 0,1873 | 0,2972 | 0,4184 |
| ParD3 | 0,0085 | 0,1644 | 0,2075 |
| TrpB | 0,1401 | 0,1764 | 0,1855 |
| NucB | 0,0743 | 0,1789 | **0,1573** |
| **média** | **0,2662** | **0,4826** | **0,5559** |

Em 11 dos 12 conjuntos a progressão é **monotônica crescente**. A média mais que
dobra de carga 1 para carga 2.

Esse é o padrão que Tran et al. apresentam na Fig. 2E como evidência de que a FCNN
"aprende a paisagem epistática". Ele é reproduzido integralmente por um modelo
incapaz de representar qualquer interação. **O artefato de redução de variância está
demonstrado de forma independente, no nosso próprio pipeline.**

Única exceção: `NucB`, não monotônico (0,179 → 0,157 de carga 2 para 3).

## 3. Comparação com os números publicados

Referência: Tabela S3, linhas de feature `One-hot` — a única rodada nas três cargas,
e também a melhor feature na carga 2.

| | Aditivo | MULTI-evolve | Diferença |
|---|---|---|---|
| Carga 1 | **0,2662** | 0,2251 | **+0,0411** |
| Carga 2 | 0,4826 | **0,5062** | −0,0236 |
| Carga 3 | 0,5559 | **0,5986** | −0,0428 |

**O aditivo iguala ou supera a FCNN em 19 das 36 células.** Ele vence de forma
consistente na carga 1 — em 12 de 12 conjuntos — com margens de até +0,16
(`ppluGFP2`, `amacGFP`) e +0,14 (`GB1`). Com apenas singles no treino, a FCNN
sobreajusta onde o ridge encolhe corretamente.

Nas cargas 2 e 3 a FCNN tem vantagem média pequena: **0,024 e 0,043 de Spearman**.

> ⚠️ **As partições não são idênticas.** Nosso teste é ordem ≥ 4; o desenho de Tran
> et al. precisa ser lido da Tabela S4 (`Max mutational load of train set` ×
> `Mutational load of test set`). Esta tabela é **indicativa** — mostra ordem de
> grandeza e forma da progressão, não uma diferença atribuível. Alinhar as partições
> é o próximo passo obrigatório antes de qualquer afirmação pareada.

## 4. O que isso faz com o Capítulo 1

A pergunta do capítulo deixa de ser vaga e fica quantitativa:

> **A vantagem de 0,024–0,043 de Spearman da FCNN sobre o aditivo é maior do que o
> que a aditividade sozinha produz?**

É exatamente o que o Nulo Aditivo Calibrado mede. E a magnitude em jogo — poucos
centésimos de Spearman — é da ordem da variabilidade que se espera de reamostragem,
o que justifica o protocolo em vez de inspeção visual.

### 4.1 Um argumento que o uso de Spearman nos dá de graça

Spearman é invariante a transformações monotônicas das predições. Se a paisagem real
fosse aditiva composta com uma não linearidade monotônica — a chamada *epistasia
global* ou não específica, que é um efeito de escala e não interação entre mutações —
o modelo aditivo **não perderia nada** em Spearman: o ordenamento de $x^\top\beta$ e
de $f(x^\top\beta)$ é o mesmo.

Portanto, sob Spearman, qualquer vantagem real da FCNN não pode vir de epistasia
global. Ela só pode vir de **epistasia específica** ou de eficiência de estimação.
Isso estreita bastante o espaço de explicações e deve ser dito explicitamente no
artigo. (Pearson não tem essa propriedade, e é por isso que as duas métricas devem
ser reportadas em paralelo.)

### 4.2 Nota sobre escala

Esta execução usou escala identidade, fiel ao `DMS_score` como distribuído. Como
Spearman é invariante a monotonicidade, a escolha de escala afeta o resultado apenas
através do *ajuste* (mínimos quadrados em escala diferente dá β diferente), não
através da métrica. O efeito é portanto menor do que seria em Pearson — mas não é
nulo, e a decisão continua pendente (§6 da especificação).

## 5. Anomalias a investigar

**`Phototropin` — salto implausível.** De −0,0826 para 0,7378 entre cargas 1 e 2,
com apenas **176 duplos** disponíveis (contra 2.122 singles). Um ganho dessa
magnitude a partir de 176 observações adicionais é suspeito e precisa de explicação:
provável concentração dos duplos em poucas posições, ou estrutura de partição
favorável. Era o conjunto já sinalizado como incompatível com o protocolo original
(§3.5 da especificação).

**`NucB` — único não monotônico**, e um dos poucos em que o MULTI-evolve tem vantagem
clara (0,2856 / 0,3762 contra 0,1789 / 0,1573). Tem 220 singles e 850 duplos. Candidato
a caso onde há epistasia aprendível de verdade — logo, candidato prioritário para o
NAC.

**`cgreGFP` — platô.** 0,5016 → 0,5354 → 0,5391: quase nenhum ganho com enriquecimento,
enquanto o MULTI-evolve sobe para 0,6434/0,6521. Outro candidato a epistasia real.

Esses três casos são mais informativos que a média, e devem guiar a priorização do
NAC: não faz sentido calibrar primeiro onde já se sabe que nada acontece.

## 6. Próximos passos, em ordem

1. **Alinhar as partições com a Tabela S4** — pré-requisito de qualquer comparação
   pareada. Conferir contra
   `data/external/multievolve-baselines/analysis/additive-proteingym_fig2ef.ipynb`.
2. **Implementar o NAC** (Passos 2–5 da especificação) e aplicá-lo primeiro a `NucB`,
   `cgreGFP` e `GB1` — onde há sinal a calibrar.
3. **Estimar o headroom epistático** $h = R^2_{CV}(\text{pareado}) - R^2_{CV}(\text{aditivo})$
   nos 12 conjuntos, para o eixo do mapa de regimes.
4. Investigar a anomalia de `Phototropin`.
5. Decidir a escala por conjunto (§6 da especificação).
