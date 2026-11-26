# Procedência das skills deste projeto

Skills de terceiros vendoradas aqui em vez de instaladas em `~/.claude/skills/`,
deliberadamente: **quais skills moldaram a análise é parte do método.** Ficando no
repositório, o commit que as introduziu e a versão exata são auditáveis por quem
reproduzir o trabalho.

## Origem

| Item | Valor |
|---|---|
| Repositório | https://github.com/K-Dense-AI/claude-scientific-skills |
| Commit | `c21d13b3cc2894680229ba9959a53281acb9200e` |
| Data do commit | 2026-11-23 |
| Licença | MIT (`LICENSE-K-Dense-AI.md`) |
| Autoria das skills | K-Dense Inc. |
| Instaladas em | 26/11/2026 |

O repositório traz **177 skills**; vendoramos **duas**. As outras 175 são de domínios
sem relação com este projeto, e trazer tudo (520 MB) seria ruído.

## O que foi instalado, e por quê

### `exploratory-data-analysis` (261 KB, v1.4)

Perfilamento local e limitado de CSV/TSV/JSON, auditoria de ausências e vazamento,
sensibilidade a transformação e outliers, e andaimes de relatório de EDA.

Dois módulos mapeiam diretamente em coisas que fizemos à mão e sem protocolo:

- **sensibilidade a transformação** — fizemos log contra min-max ad hoc em
  `RESULTADOS_ESCALA.md`;
- **auditoria de ausências e vazamento** — tivemos o filtro de estringência e os
  zeros no piso do ensaio, e nenhum dos dois foi auditado sistematicamente.

### `statistical-analysis` (136 KB, v2.0)

Seleção de teste, verificação de pressupostos, tamanhos de efeito, poder, alternativas
bayesianas e padrões de reporte.

Vale mais do que parece para este projeto, por um motivo concreto: o Artigo 1 reporta
Wilcoxon, intervalos de confiança e testes de sinais em dezenas de células, e nós
mesmos já tivemos de **retirar duas afirmações** por fragilidade estatística. E há uma
questão aberta que é exatamente do escopo desta skill — o nulo calibrado tem poder
tão alto que efeitos triviais saem significativos (`RESULTADOS_NAC.md` §1). As
referências `effect_sizes_and_power.md` e `reporting_standards.md` servem de
contraprova antes da submissão.

## Postura de segurança

As duas skills declaram tratar cada célula, cabeçalho e string de metadado como **dado
não confiável**, sem seguir instruções embutidas nem passar texto derivado de arquivo
para o shell. Isso importa aqui: nossos dados vêm de terceiros (Zenodo).

**Compromisso de uso:** os 14 scripts Python que acompanham as skills (3.100 linhas
somadas) **não serão executados sem leitura prévia**. Eles são código de terceiros, e
a licença MIT não é auditoria.

| Skill | Scripts | Linhas |
|---|---|---|
| `exploratory-data-analysis` | 13 | ~2.750 |
| `statistical-analysis` | 1 | 352 |

## O que foi avaliado e recusado

**[VLSIDA/vlsida-skills](https://github.com/VLSIDA/vlsida-skills)**, avaliado em 26/11.
Seis skills: quatro de VLSI e infraestrutura (`openroad-tcl`, `sdc-sta`, `gcloud`,
`nautilus-nrp`), sem relação com o projeto. Duas de interesse **futuro**, não
instaladas ainda:

- `paper-writing` — convenções de LaTeX, quando houver `.tex`. Ressalva: são as
  convenções de um laboratório de arquitetura de computadores; parte é universal
  (legenda afirma a conclusão, unidade em todo eixo), parte é específica de campo e
  pode conflitar com o estilo de uma revista de biologia.
- `brutal-review` — revisor final, explicitamente "as últimas horas antes da
  submissão". Prematuro.

Licença BSD-3-Clause. O `install.sh` deles apenas cria symlinks em
`~/.claude/skills/`, é idempotente e não sobrescreve.

## Já disponíveis na sessão, não vendoradas

`dataviz` (Anthropic) cobre a camada de gráficos e deve ser carregada antes do
primeiro gráfico da exploratória. Não precisa instalação.
