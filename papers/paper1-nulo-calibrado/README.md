# Artigo 1 — Escala ou interação? Decompondo a vantagem de modelos epistáticos em MLDE

> **Leia [`SINTESE.md`](SINTESE.md) primeiro.** É o documento primário do capítulo;
> os demais são detalhamento.

**Pergunta.** De que consiste a vantagem de um modelo flexível sobre o nulo aditivo
na predição de multimutantes? Quanto dela é **epistasia global** — um efeito de
escala, sem interação entre mutações — e quanto é **epistasia específica**?

**O instrumento.** Spearman é invariante a transformações monotônicas das predições;
Pearson não. Um ganho que aparece em Pearson e não em Spearman é escala. Um ganho em
Spearman não pode ser escala. Tran et al. reportam as duas métricas em paralelo sem
explorar o contraste.

**A resposta, em uma linha.** Metade da vantagem da FCNN sobre o aditivo é
reproduzível por um modelo sem nenhuma capacidade de interação; o que sobra é pequeno,
inconsistente entre conjuntos e não extrapola.

**Entregas.** (1) O software do Nulo Aditivo Calibrado, agnóstico a pipeline.
(2) A decomposição escala *vs* interação — nos 12 conjuntos via FCNN e modelo global,
nos 5 identificáveis via incremento pareado calibrado. (3) O limite de
identificabilidade como fronteira declarada do método.

**Nota de percurso.** A pergunta acima **não** era a original, e as entregas foram
revisadas. Ver `ESPECIFICACAO.md` §7 — o texto original fica como registro, e a
divergência está documentada em vez de apagada.

## Estado

- [x] Marco zero — o aditivo reproduz a progressão da Fig. 2E (12 conjuntos)
- [x] Protocolo de Tran et al. reconstruído e comparação pareada (288 células)
- [x] FCNN reexecutada no nosso pipeline (24 tarefas, HPC)
- [x] Baseline de epistasia global (12 conjuntos, 3 cargas)
- [x] Nulo calibrado — **2 de 15 células** (GB1 e TrpB, carga 3)
- [ ] Nulo calibrado nas 13 células restantes
- [ ] Sensibilidade a `val_split` e a sementes de fold
- [ ] Sensibilidade ao $\sigma$ da ordem 4 no nulo
- [ ] Replicação em escala log

Os experimentos pendentes estão preparados como *array jobs* em `hpc_fcnn_rerun/`.

## Código

| Arquivo | O que faz |
|---|---|
| `src/landscape.py` | carregamento e matriz de desenho binária |
| `src/milestone0_additive.py` | marco zero |
| `src/aligned_protocol.py` | protocolo de Tran et al. replicado |
| `src/compare_to_s4.py`, `src/compare_to_tran.py` | comparação com os números publicados |
| `src/analyze_deltas.py` | interpolação *vs* extrapolação, assimetria Pearson/Spearman |
| `src/verify_hpc_results.py` | verificação independente dos resultados do HPC |
| `src/global_epistasis.py` | baseline de epistasia global |
| `src/compare_global_vs_fcnn.py` | quanto da vantagem da FCNN o modelo global recupera |
| `src/calibrated_null.py` | **o NAC** |
