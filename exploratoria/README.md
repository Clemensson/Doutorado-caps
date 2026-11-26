# Análise exploratória do benchmark

Iniciativa aberta em 26/11/2026, sobre os 12 conjuntos DMS que Tran et al.
distribuíram em `data/external/zenodo-17620759/` (catálogo em `data/README.md`).

## Por que isto existe

O Artigo 1 foi direto para a modelagem. Nunca olhamos os dados — o que existe é um
inventário de contagens, não uma exploração. E o capítulo acumulou **quatro perguntas
que só os dados respondem**, todas levantadas por resultados de modelagem e nenhuma
resolvida:

1. **Qual é a forma da não linearidade monotônica?** Sabemos que não é censura e que
   só 15–26% é logarítmica (`RESULTADOS_ESCALA.md`). O resto não tem nome. A curva de
   $y$ contra $x^\top\hat\beta$ **é** a função que a isotônica aprende — plotá-la
   nomearia a forma, e a hipótese registrada é uma sigmoide tipo Hill.
2. **Por que o σ decresce com a ordem mutacional?** Medimos 0,093 / 0,062 / 0,050 em
   GB1 e assumimos como dado. Não sabemos a causa, e isso sustenta a política de σ do
   nulo calibrado.
3. **Por que GB1 e TrpB têm epistasia específica e os outros não?** A hipótese é
   densidade de duplos medidos por par de posições, nunca quantificada.
4. **Por que o ridge pareado piora o ordenamento onde a FCNN melhora?**
   (`RESULTADOS_NAC_FCNN.md`) A hipótese é sobreajuste, e a estrutura dos dados diria.

**Esta pasta não é um quinto artigo.** É a exploração que devia ter vindo antes, e que
agora tem perguntas precisas em vez de "olhar os dados".

## A lição de percurso que isto incorpora

O Artigo 1 derivou por acumular análises bem-feitas sem conferir contra o objetivo
(`ESPECIFICACAO.md` §7.2). Por isso cada item abaixo tem **a pergunta que responde** e
**o que decide com a resposta**. Item sem isso não entra.

## Perguntas, em ordem de valor

| # | Pergunta | Decide |
|---|---|---|
| 1 | Forma de $y$ contra $x^\top\hat\beta$, por conjunto | nomeia a não linearidade; se for sigmoide, qual família ajustar como baseline explícito |
| 2 | Distribuição de $y$ por ordem mutacional; onde há piso e teto | explica o σ decrescente e a censura |
| 3 | Densidade de duplos medidos por par de posições | explica por que GB1/TrpB têm interação estimável |
| 4 | Completude combinatória real por posição | fecha a pendência de `data/README.md` §4 sobre o ParD3 |
| 5 | Sobreposição de mutações entre ordens | quantifica o custo do filtro de estringência |

A pergunta 1 é a de maior valor: ela é a única que pode fechar a lacuna aberta do
Artigo 1.

## Estrutura

| Diretório | Conteúdo |
|---|---|
| `src/` | scripts de análise |
| `figuras/` | figuras geradas (não versionadas) |
| `resultados/` | tabelas geradas (não versionadas) |
| `notebooks/` | exploração interativa |

## Ferramentas

A skill **`dataviz`** desta sessão deve ser carregada antes do primeiro gráfico — é
desenhada para isso e garante consistência de paleta e legibilidade em claro e escuro.

Sobre o repositório [VLSIDA/vlsida-skills](https://github.com/VLSIDA/vlsida-skills),
avaliado em 26/11: das seis skills, quatro são de VLSI e infraestrutura
(`openroad-tcl`, `sdc-sta`, `gcloud`, `nautilus-nrp`) e **nenhuma serve à exploração**.
Duas servem mais adiante: `paper-writing` (convenções de LaTeX) quando houver `.tex`, e
`brutal-review` (revisor final) quando o manuscrito estiver quase pronto. O
`install.sh` apenas cria symlinks em `~/.claude/skills/`, é idempotente e não
sobrescreve; licença BSD-3-Clause. Nota: o `paper-writing` codifica convenções de um
laboratório de arquitetura de computadores — parte é universal, parte é específica de
campo e pode conflitar com o estilo de uma revista de biologia. Checklist, não lei.
