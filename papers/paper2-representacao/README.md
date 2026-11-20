# Artigo 2 — Representação importa?

**Pergunta.** Alguma representação captura epistasia que o one-hot não captura,
**acima do nulo calibrado** do Artigo 1?

**Motivação.** Limitação (iii) de Koo et al.: o one-hot do MULTI-evolve não carrega
contatos resíduo-resíduo nem informação estrutural.

**Desenho.** Ablação controlada — one-hot vs. descritores físico-químicos vs.
embeddings de PLM vs. contatos estruturais, com as mesmas partições e o mesmo nulo.
XGBoost e Ridge com interações pareadas entram como sondas de qual classe de função é
necessária, não como competidores da FCNN.

**Nota.** Um resultado negativo honesto é publicável, e é o desfecho mais provável.
LoRA e *fine-tuning* só se liberam se este capítulo mostrar que representação importa.

Estado: não iniciado. Depende do Artigo 1.

---

## ⚠️ Achado de 2026-11-20 que exige redefinir este capítulo

A Tabela S3 do suplementar de Tran et al. mostra que **sete representações foram
testadas**, incluindo embeddings de PLM, e que o **one-hot venceu todas** na carga de
treino 2:

| Feature | Spearman-Test (carga 2) |
|---|---|
| **One-hot** | **0,5062** |
| AAidx | 0,4927 |
| Georgiev | 0,4801 |
| Ankh Large | 0,4727 |
| ESM2-15B | 0,4560 |
| ProtT5-XL | 0,4284 |
| ESM2-3B | 0,3772 |

A crítica de Koo et al. — de que o one-hot limita a capacidade representacional e que
embeddings de PLM capturariam contatos e estrutura — **já tem resposta no próprio
suplementar do artigo, e é negativa**. O capítulo como formulado perguntaria algo já
respondido.

**Reorientação proposta (aguardando decisão):** o achado deixa de ser "representação
ajuda?" e passa a ser que **o eixo de representação é plano**. Sete representações
muito diferentes, incluindo PLMs de 15 bilhões de parâmetros, colapsam numa faixa de
0,13 de Spearman — e a mais pobre delas ganha. Se nenhuma informação adicional move o
desempenho, isso é evidência de que o modelo não extrai estrutura de interação de
nenhuma delas, convergindo com a tese do Artigo 1.

Note que essas comparações também nunca foram feitas contra um nulo aditivo
calibrado, o que dá ao capítulo um ângulo próprio: aplicar o NAC do Artigo 1 ao eixo
de representação e mostrar que a faixa inteira é indistinguível do nulo.
