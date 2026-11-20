# Artigo 3 — O viés de nomeação

**Pergunta.** Que fração dos melhores multimutantes é **inalcançável por construção**
quando a campanha nomeia apenas singles benéficas?

**Motivação.** Limitação (ii) de Koo et al.: o MULTI-evolve amostra o espaço em torno
de mutações benéficas, perdendo caminhos em que o ótimo exige mutações neutras ou
deletérias isoladamente. Território que o preprint do DeWitt não toca.

**Desenho — exato em 4 posições, aproximado em ordem alta.**

- *Exato:* `TRPB1_THEMA_Tm9D8_Johnston_2024` (99,5% completo) e `SPG1_STRSG_Wu_2016`
  (GB1, 93,4%) são paisagens de 4 posições × 19 substituições. Enumeração completa:
  simular a nomeação top-k benéficas contra nomeações que incluam neutras e
  deletérias, e contar diretamente. Sem amostragem e sem modelo interposto.
- *Aproximado:* `HIS7_YEAST_Pokusaeva_2019` (ordem até 28) e `PHOT_CHLRE_Chen_2023`
  (ordem até 15) testam se o padrão persiste na faixa de ordem que o MULTI-evolve
  realmente usa, com o viés de amostragem declarado.

A concordância entre os dois regimes é resultado em si.

**Limitação a declarar.** Paisagens completas existem só em 4 posições; a ordem 5–9
é acessível apenas de forma esparsa.

**Por que importa.** Se a fração for grande, é um limite do desenho da campanha que
nenhum ganho de arquitetura resolve.

Estado: não iniciado. Viabilidade **confirmada** pelo inventário
(`data/README.md`, §3.1).
