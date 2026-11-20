# Catálogo de dados

Inventário das fontes externas do projeto. **Nada em `external/` é versionado**
(ver `.gitignore`): tudo é re-obtenível pelos DOIs e commits registrados aqui.
Catálogos derivados, que são texto e pequenos, ficam em `catalog/` e vão para o git.

Levantamento feito em 2026-11-20.

---

## 1. Procedência

| Fonte | Identificador | Estado local | Conteúdo |
|---|---|---|---|
| Dados de benchmarking (Tran et al.) | DOI [10.5281/zenodo.17620759](https://doi.org/10.5281/zenodo.17620759) | `external/zenodo-17620759/` — **12/12 arquivos, 375 MB** | Conjuntos DMS combinatórios |
| Tabelas suplementares (Tran et al.) | DOI [10.5281/zenodo.18240028](https://doi.org/10.5281/zenodo.18240028) | `external/zenodo-18240028/` — **16/16 arquivos, 8,5 MB** | Tabelas S1–S16 |
| Código oficial MULTI-evolve | [VincentQTran/MULTI-evolve](https://github.com/VincentQTran/MULTI-evolve) | `external/multievolve-code/` | commit `5cdb074`, 2026-02-27 |
| Reanálise com nulos aditivos | [dewitt-lab/multievolve-baselines](https://github.com/dewitt-lab/multievolve-baselines) | `external/multievolve-baselines/` | commit `e733e6f`, **2026-11-11** |

O registro 17620759 declara que os conjuntos vêm do [ProteinGym](https://proteingym.org/)
e de três estudos adicionais (DOIs `10.1016/j.cels.2025.101236`,
`10.1073/pnas.2400439121`, `10.1038/s41467-023-39022-2`).

**Atenção à data do `multievolve-baselines`:** último commit em 2026-11-11, nove dias
antes deste levantamento, com um diretório `patches/` que modifica o MULTI-evolve. O
grupo do DeWitt está ativamente trabalhando nisso. Reavaliar antes de fixar escopo.

### Nota reprodutibilidade
`files-archive` da API do Zenodo retorna 403; os arquivos foram baixados
individualmente a partir dos links `self` de cada entrada. Os nomes das tabelas
suplementares contêm espaços (`%20` nas URLs).

---

## 2. Os 12 conjuntos DMS — inventário

Gerado por `scripts/catalog_dms.awk` → `catalog/dms_catalog.tsv`.
Esquema dos CSVs (ProteinGym): `mutant,mutated_sequence,DMS_score,DMS_score_bin`,
com `mutant` em tokens separados por `:` (ex. `L59M:W60T:K64W`). Ordem mutacional
= número de tokens.

| Conjunto | Variantes | Ordem máx | Pos. | Muts únicas | Ord. 1 | 2 | 3 | 4 | 5+ | Faixa de score |
|---|---|---|---|---|---|---|---|---|---|---|
| `SPG1_STRSG_Wu_2016` (GB1) | 149.360 | 4 | **4** | 76 | 76 | 2.091 | 26.019 | 121.174 | 0 | 0 – 8,76 |
| `TRPB1_THEMA_Tm9D8_Johnston_2024` | 159.128 | 4 | **4** | 76 | 76 | 2.166 | 27.368 | 129.518 | 0 | 0 – 1,00 |
| `F7YBW8_MESOW_Aakre_2015` (ParD/ParE) | 9.192 | 4 | **4** | 37 | 37 | 499 | 2.798 | 5.858 | 0 | −0,05 – 1,20 |
| `CAPSD_AAV2S_Sinai_2021` | 42.328 | 28 | 28 | 532 | 532 | 10.833 | 6.906 | 6.646 | 17.411 | −9,54 – 9,54 |
| `HIS7_YEAST_Pokusaeva_2019` | 496.137 | 28 | 171 | 1.597 | 168 | 1.475 | 7.627 | 25.927 | **460.940** | 0 – 2,33 |
| `PHOT_CHLRE_Chen_2023` | 167.529 | 15 | 118 | 2.122 | 2.122 | 176 | 978 | 3.565 | **160.688** | 0,02 – 1,78 |
| `GFP_AEQVI_Sarkisyan_2016` (avGFP) | 51.714 | 15 | 233 | 1.810 | 1.084 | 12.777 | 12.336 | 9.387 | 16.130 | 1,28 – 4,12 |
| `Q8WTC7_9CNID_Somermeyer_2022` | 33.510 | 43 | 237 | 1.638 | 1.201 | 11.260 | 11.641 | 5.762 | 3.646 | 449 – 18.689 |
| `Q6WV13_9MAXI_Somermeyer_2022` | 31.401 | 13 | 221 | 1.459 | 1.141 | 15.992 | 8.762 | 3.575 | 1.931 | 590 – 27.865 |
| `D7PM05_CLYGR_Somermeyer_2022` | 24.515 | 23 | 234 | 1.651 | 1.169 | 10.148 | 6.315 | 3.417 | 3.466 | 590 – 40.087 |
| `VH14_Li_2023` | 35.888 | 19 | 35 | 665 | 436 | 2.693 | 15.569 | 5.213 | 11.977 | −6,71 – 2,42 |
| `Q65J43_BACLD_g4_Thomas_2025` | 15.403 | 23 | 110 | 1.925 | 220 | 850 | 1.048 | 894 | 12.391 | 1,00 – 3,87 |

---

## 3. Leitura científica do inventário

### 3.1 O Artigo 3 (viés de nomeação) é viável — e tem dois conjuntos ideais

Dois conjuntos são **paisagens combinatórias praticamente completas em 4 posições**,
com 19 substituições por posição (76 mutações únicas = 4 × 19), ou seja 20⁴ = 160.000
combinações possíveis:

- `TRPB1_THEMA_Tm9D8_Johnston_2024` — 159.128 medidas = **99,5% completo**
- `SPG1_STRSG_Wu_2016` (GB1) — 149.360 medidas = **93,4% completo**

Isso permite o desenho exato que o Artigo 3 exige: enumerar a paisagem inteira,
simular a nomeação do MULTI-evolve (top-k singles benéficas), e medir **exatamente**
que fração dos melhores multimutantes fica inalcançável por construção. Sem
amostragem e sem modelo interposto — contagem direta.

Limitação a declarar: com 4 posições, a ordem máxima é 4, enquanto o MULTI-evolve
opera em 5–9 mutações. A análise exata não escala para a ordem de interesse.

### 3.2 Os conjuntos de ordem alta são o complemento necessário — mas são esparsos

`HIS7_YEAST` (ordem até 28, 460.940 variantes de ordem ≥5) e `PHOT_CHLRE`
(ordem até 15, 160.688 de ordem ≥5) alcançam a faixa de ordem que interessa,
mas são amostras esparsas de espaços astronômicos, não paisagens completas.
Servem para testar se o padrão achado exatamente nos conjuntos de 4 posições
persiste em ordem alta — de forma aproximada, com o viés de amostragem declarado.

Desenho que isso sugere: **exato em 4 posições, aproximado em ordem alta**, com a
concordância entre os dois regimes como o próprio resultado.

### 3.3 Dois conjuntos têm quase nenhum duplo — cuidado

`PHOT_CHLRE_Chen_2023` tem 2.122 singles mas só **176 duplos**, e
`Q65J43_BACLD_g4_Thomas_2025` tem 220 singles e 850 duplos. O MULTI-evolve treina
em singles + duplos. Esses conjuntos não sustentam o protocolo de treino original e
precisam ser tratados à parte, ou excluídos com justificativa explícita.

### 3.4 Escalas de score são heterogêneas — e isso é metodologicamente crítico

Os três conjuntos `Somermeyer_2022` têm scores em centenas a dezenas de milhares
(brilho bruto); os demais estão em faixas pequenas, alguns já em log. O argumento
central do preprint do DeWitt é que **aditividade é esperada em escala logarítmica**
(contribuições termodinâmicas independentes). Comparar modelo aditivo e FCNN em
escala bruta vs. log não é a mesma comparação. Fixar e justificar a transformação
por conjunto é pré-requisito do Artigo 1, não um detalhe de pré-processamento.

### 3.5 Sobre recursos computacionais

375 MB no total, maior arquivo 130 MB, e os modelos em questão são aditivos, Ridge,
XGBoost e FCNNs pequenas. **O núcleo do projeto roda em CPU.** GPU só seria
necessária para gerar embeddings de PLM no Artigo 2, e mesmo isso é pré-computável
uma vez e reutilizável.

---

## 4. Pendências

- [ ] Obter Tran et al., *Science* 2026 (artigo original) — ainda ausente de `literature/`
- [ ] Verificar completude combinatória de `F7YBW8_MESOW_Aakre_2015` por posição (37 mutações não se distribuem como 4 × 19)
- [ ] Conferir quais conjuntos já estão em escala log e quais não
- [ ] Cruzar este inventário com `Table S7 Benchmarking datasets.xlsx` e `Table S4 ... split by mutational load.xlsx`
- [ ] Instalar Python 3 (ver `docs/ambiente.md`) — ausente na máquina
