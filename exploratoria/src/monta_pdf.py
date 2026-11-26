"""Monta o relatorio didatico em HTML e imprime em PDF pelo Chrome headless.

Nao ha pandoc, LaTeX nem biblioteca de PDF nesta maquina; o Chrome esta disponivel e
imprime HTML com controle total de tipografia e quebra de pagina.

As figuras entram embutidas em base64 para o PDF ficar autocontido — util para
circular no laboratorio sem anexos soltos.

Uso:
    python -I exploratoria/src/monta_pdf.py --fig exploratoria/figuras \\
        --res exploratoria/resultados --out exploratoria/RELATORIO_EDA.pdf
"""

from __future__ import annotations

import argparse
import base64
import subprocess
from pathlib import Path

import pandas as pd

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", "DejaVu Sans", sans-serif; color: #1a1a1a;
       font-size: 10.5pt; line-height: 1.5; margin: 0; }
h1 { font-size: 21pt; line-height: 1.2; margin: 0 0 4pt; color: #0e3d7e; }
h2 { font-size: 14pt; margin: 20pt 0 6pt; color: #0e3d7e;
     border-bottom: 2px solid #cce3fd; padding-bottom: 3pt; }
h3 { font-size: 11.5pt; margin: 14pt 0 4pt; color: #1757ac; }
p { margin: 0 0 7pt; }
.sub { color: #6b6b6b; font-size: 10pt; margin-bottom: 14pt; }
.capa { border-left: 5px solid #257de0; padding-left: 12pt; margin-bottom: 18pt; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 8pt 0 12pt; }
th { background: #f2f7fe; text-align: left; padding: 5pt 6pt;
     border-bottom: 2px solid #9dc8f7; font-weight: 600; }
td { padding: 4pt 6pt; border-bottom: 1px solid #ececec; }
tr.destaque td { background: #f2f7fe; font-weight: 600; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
figure { margin: 10pt 0 14pt; page-break-inside: avoid; }
figure img { width: 100%; border: 1px solid #ececec; }
figcaption { font-size: 9pt; color: #4a4a4a; margin-top: 5pt;
             border-left: 3px solid #257de0; padding-left: 8pt; }
.caixa { background: #f7f9fc; border-left: 4px solid #257de0;
         padding: 9pt 12pt; margin: 10pt 0; font-size: 10pt; }
.alerta { background: #fdf4f4; border-left: 4px solid #dc3c3d; }
.kpis { display: flex; gap: 10pt; margin: 14pt 0 18pt; }
.kpi { flex: 1; border: 1px solid #cce3fd; border-radius: 4pt;
       padding: 9pt 11pt; background: #fbfdff; }
.kpi .v { font-size: 20pt; font-weight: 700; color: #0e3d7e; line-height: 1.1; }
.kpi .r { font-size: 8.5pt; color: #6b6b6b; margin-top: 3pt; }
.quebra { page-break-before: always; }
.rodape { margin-top: 20pt; padding-top: 8pt; border-top: 1px solid #ececec;
          font-size: 8.5pt; color: #6b6b6b; }
code { background: #f2f2f2; padding: 1pt 3pt; border-radius: 2pt; font-size: 9pt; }
"""


def img(p: Path) -> str:
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f'<img src="data:image/png;base64,{b64}">'


def tabela(df: pd.DataFrame, cols: list[str], destacar=None) -> str:
    destacar = destacar or set()
    h = "".join(f"<th>{c}</th>" for c in cols)
    linhas = []
    for _, r in df.iterrows():
        cls = ' class="destaque"' if r.iloc[0] in destacar else ""
        tds = "".join(
            f'<td class="num">{r[c]}</td>' if i else f"<td>{r[c]}</td>"
            for i, c in enumerate(cols))
        linhas.append(f"<tr{cls}>{tds}</tr>")
    return f"<table><thead><tr>{h}</tr></thead><tbody>{''.join(linhas)}</tbody></table>"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig", required=True)
    ap.add_argument("--res", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    F, R = Path(args.fig), Path(args.res)

    rot = {"HIS7_YEAST_Pokusaeva_2019": "IGP dehydratase",
           "TRPB1_THEMA_Tm9D8_Johnston_2024": "TrpB",
           "F7YBW8_MESOW_Aakre_2015": "ParD3", "SPG1_STRSG_Wu_2016": "GB1",
           "GFP_AEQVI_Sarkisyan_2016": "avGFP", "CAPSD_AAV2S_Sinai_2021": "AAV2 VP1",
           "VH14_Li_2023": "scFv", "Q8WTC7_9CNID_Somermeyer_2022": "amacGFP",
           "Q6WV13_9MAXI_Somermeyer_2022": "ppluGFP2",
           "D7PM05_CLYGR_Somermeyer_2022": "cgreGFP",
           "Q65J43_BACLD_g4_Thomas_2025": "NucB",
           "PHOT_CHLRE_Chen_2023": "Phototropin"}
    rec = {"IGP dehydratase", "TrpB", "ParD3", "GB1"}

    e = pd.read_csv(R / "eda_epistasia.tsv", sep="\t")
    e["Conjunto"] = e.conjunto.map(rot)
    e["Candidatos"] = e.n_compensatorio.astype(int)
    e["Taxa"] = (e.frac_compensatorio * 100).map(lambda v: f"{v:.2f}%")
    e["Sem as partes"] = (e.frac_sem_todos_singles * 100).map(lambda v: f"{v:.1f}%")
    e["Supera as partes"] = (e.frac_supera_as_partes * 100).map(lambda v: f"{v:.1f}%")
    tab_e = e.sort_values("n_compensatorio", ascending=False)

    c = pd.read_csv(R / "eda_colunas.tsv", sep="\t")
    s = c[c.coluna == "DMS_score"].copy()
    s["Conjunto"] = s.conjunto.map(rot)
    s["n"] = s.n.map(lambda v: f"{v:,}".replace(",", "."))
    for col in ("mediana", "iqr", "mad"):
        s[col.upper() if col != "mediana" else "Mediana"] = s[col].map(
            lambda v: f"{v:,.4g}".replace(",", "."))
    tab_s = s.sort_values("n", ascending=False)

    html = f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<style>{CSS}</style><body>

<div class="capa">
<h1>Os 12 conjuntos do benchmark: o que os dados permitem perguntar</h1>
<div class="sub">Relatório de primeiro olhar &middot; 26 de novembro de 2026 &middot;
para discussão no laboratório</div>
</div>

<div class="caixa">
<b>Para quem está chegando agora.</b> Cada conjunto destes é uma
<i>varredura mutacional profunda</i>: pegaram uma proteína, fizeram milhares de
versões dela com uma ou mais mutações, e mediram o quanto cada versão ainda funciona.
Cada linha da tabela é uma variante; a coluna <code>DMS_score</code> é o quanto ela
funciona; a coluna <code>mutant</code> diz quais mutações ela carrega.
</div>

<h2>A pergunta que queremos responder</h2>
<p><b>Epistasia compensatória</b> é quando duas mutações que, sozinhas, são ruins ou
indiferentes, juntas produzem algo melhor que qualquer uma delas. Uma "conserta" a
outra.</p>
<p>Exemplo imaginário: a mutação A sozinha deixa a proteína pior. A mutação B sozinha
também. Mas A+B juntas ficam melhores que A, que B, e que a proteína original. Isso é
compensação — e é interessante porque nenhum modelo que apenas <i>soma</i> os efeitos
individuais consegue prever.</p>
<p><b>Para procurar isso nos dados, precisamos de duas coisas ao mesmo tempo:</b>
que existam combinações desse tipo, e que as mutações isoladas tenham sido medidas —
sem saber o efeito de A sozinha, não dá para dizer que ela era ruim.</p>

<h2>Veredicto</h2>
<div class="kpis">
  <div class="kpi"><div class="v">4 de 12</div>
    <div class="r">conjuntos sustentam a pergunta</div></div>
  <div class="kpi"><div class="v">0,73%</div>
    <div class="r">a melhor taxa de candidatos</div></div>
  <div class="kpi"><div class="v">1.534</div>
    <div class="r">candidatos no melhor conjunto</div></div>
  <div class="kpi"><div class="v">87%</div>
    <div class="r">no piso do ensaio, no pior caso</div></div>
</div>

{tabela(tab_e, ["Conjunto", "Candidatos", "Taxa", "Sem as partes",
                "Supera as partes"], rec)}
<p class="sub">Linhas destacadas são as recomendadas. <b>Candidatos</b>: combinações
em que todas as mutações isoladas ficam abaixo da mediana e a combinação fica no decil
superior. <b>Sem as partes</b>: multimutantes que não podem ser analisados porque
alguma mutação constituinte não foi medida sozinha.</p>

<figure>{img(F / 'fig3_candidatos.png')}
<figcaption><b>Dois jeitos de olhar o mesmo fato.</b> À esquerda, quantos candidatos
cada conjunto tem; à direita, que fração das combinações analisáveis eles
representam. IGP dehydratase ganha em número absoluto, ParD3 em taxa.
</figcaption></figure>

<div class="caixa alerta">
<b>O sinal é raro em todo lugar.</b> No melhor conjunto, 0,73% das combinações são
candidatas. Isso muda o tipo de problema: não é regressão comum, é
<b>classe desbalanceada</b>. Métricas de erro médio vão esconder o fenômeno.
</div>

<div class="quebra"></div>
<h2>1. Estatísticas por coluna</h2>
<p>Os 12 arquivos têm o mesmo esquema de quatro colunas. <b>Nenhum valor ausente, em
nenhuma coluna, em nenhum conjunto.</b> Nenhuma variante duplicada.</p>
{tabela(tab_s, ["Conjunto", "n", "Mediana", "IQR", "MAD"])}
<p class="sub">IQR e MAD são medidas de dispersão robustas: metade das variantes cai
dentro do IQR. Usamos elas em vez do desvio-padrão porque várias distribuições têm
cauda longa, e aí a média engana — em GB1 a média é 27 vezes a mediana.</p>

<h2>2. Distribuições</h2>
<figure>{img(F / 'fig1_massa_no_piso.png')}
<figcaption><b>Em cinco conjuntos, boa parte das variantes está "morta" no limite de
detecção do ensaio.</b> Isso não é dado faltando — é o ensaio dizendo "não dá para
medir abaixo disto". Tratar como ausente e imputar falsificaria o fenômeno.
</figcaption></figure>

<figure>{img(F / 'fig4_score_vs_ordem.png')}
<figcaption><b>Quanto mais mutações, pior a proteína — em 11 dos 12 conjuntos.</b>
A exceção, scFv, sobe: ρ=+0,67. Cada painel tem escala própria; o que se lê aqui é a
forma da curva, não o nível.</figcaption></figure>

<div class="quebra"></div>
<h2>3. Correlações que merecem atenção</h2>
<h3>A coluna <code>DMS_score_bin</code> não traz informação nova</h3>
<p>Testamos se ela é apenas um corte no <code>DMS_score</code>. <b>É — com coerência
de 1,000 nos 12 conjuntos</b>, e recuperamos os limiares exatos.</p>
<div class="caixa alerta"><b>Risco de vazamento.</b> Usar
<code>DMS_score_bin</code> como alvo enquanto <code>DMS_score</code> está entre os
atributos é prever a resposta a partir dela mesma. O modelo pareceria excelente e não
teria aprendido nada.</div>

<h3>O score cai com o número de mutações</h3>
<p>Negativo em 11 dos 12 (de −0,04 a −0,55). A exceção é o scFv, com +0,67 — ver o
problema P3.</p>

<h2>4. Problemas encontrados</h2>
<figure>{img(F / 'fig2_decomponibilidade.png')}
<figcaption><b>P1, o mais grave: em NucB e scFv quase nenhuma combinação pode ser
decomposta.</b> Sem o efeito das mutações isoladas, a pergunta sobre compensação não
pode nem ser formulada nessas variantes.</figcaption></figure>

<figure>{img(F / 'fig5_escalas.png')}
<figcaption><b>P4: as escalas são incompatíveis.</b> Três conjuntos estão em
intensidade bruta de fluorescência, na casa dos milhares; outros em frações abaixo de
0,01. O NucB aparece como anotação porque seu IQR é exatamente zero — metade das
variantes tem o mesmo valor.</figcaption></figure>

<h3>Os sete problemas, por impacto</h3>
<table><thead><tr><th>#</th><th>Problema</th><th>Onde</th><th>Gravidade</th></tr>
</thead><tbody>
<tr class="destaque"><td>P1</td><td>Multimutantes sem as mutações isoladas medidas</td>
<td>NucB 95,4% · scFv 84,1% · IGP 48,7%</td><td>crítico</td></tr>
<tr class="destaque"><td>P2</td><td>NucB quase inteiramente censurado (IQR e MAD = 0)</td>
<td>87% no piso</td><td>crítico</td></tr>
<tr class="destaque"><td>P3</td><td>scFv não parece varredura aleatória: mais mutações,
melhor fenótipo</td><td>ρ=+0,67</td><td>crítico</td></tr>
<tr><td>P4</td><td>Escalas incompatíveis entre conjuntos</td>
<td>6 ordens de magnitude</td><td>alto</td></tr>
<tr><td>P5</td><td><code>DMS_score_bin</code> redundante e com risco de vazamento</td>
<td>todos os 12</td><td>médio</td></tr>
<tr><td>P6</td><td>Linhas ordenadas: ler o início do arquivo dá amostra enviesada</td>
<td>NucB, scFv, Phototropin</td><td>médio</td></tr>
<tr><td>P7</td><td>Dois tokens malformados</td><td>de ~1,10 milhão</td>
<td>desprezível</td></tr>
</tbody></table>

<div class="caixa"><b>O que NÃO é problema, e vale dizer.</b> Zero valores ausentes.
Zero duplicatas. Comprimento de sequência constante dentro de cada conjunto. E
consistência de 100% entre a mutação declarada e a sequência, verificada em
~1,10 milhão de casos. <b>A qualidade mecânica dos dados é alta — os problemas são
estruturais, não de limpeza.</b></div>

<div class="quebra"></div>
<h2>5. Próximos passos</h2>
<h3>Decisões para a equipe tomar agora</h3>
<ol>
<li><b>Restringir a 4 conjuntos:</b> IGP dehydratase, TrpB, ParD3 e, marginalmente,
GB1. Descartar NucB e scFv por escrito, com o motivo.</li>
<li><b>Tratar como problema de classe rara.</b> 0,73% no melhor caso.</li>
<li><b>Excluir as ordens totalmente censuradas.</b> Em IGP e cgreGFP, 100% das
variantes de ordem máxima estão no piso — ali o ensaio não discrimina mais nada.</li>
<li><b>Não usar <code>DMS_score_bin</code></b> como atributo nem como alvo.</li>
<li><b>Normalizar por conjunto</b>, de forma declarada, antes de qualquer análise
conjunta.</li>
</ol>

<h3>Análises que faltam, em ordem de valor</h3>
<table><thead><tr><th>#</th><th>Análise</th><th>O que decide</th></tr></thead><tbody>
<tr><td>1</td><td><s>Curva do score contra a soma dos efeitos individuais</s></td><td><b>FEITA</b> — ver seção 6</td></tr>
<tr class="destaque"><td>1b</td><td>Ajustar uma sigmoide paramétrica de 4 parâmetros</td><td>dá significado biofísico ao piso, teto e inclinação</td></tr>
<tr><td>2</td><td>Densidade de pares de posições com duplos medidos</td>
<td>por que alguns conjuntos sustentam interação e outros não</td></tr>
<tr><td>3</td><td>Caracterizar os 1.534 candidatos do IGP</td>
<td>são posições específicas? poucas mutações recorrentes?</td></tr>
<tr><td>4</td><td>Incerteza de medição nos candidatos</td>
<td>hoje o corte é determinístico e pode estar contando ruído</td></tr>
</tbody></table>

<div class="caixa alerta">
<b>Ressalva honesta sobre as definições.</b> "Supera as partes" e "candidato
compensatório" são definições <b>nossas</b>, não padrão da literatura, e estão
escritas no código. Nenhuma das duas incorpora incerteza de medição: são cortes
determinísticos. Com 87% de massa no piso em alguns conjuntos, parte do que contamos
pode ser ruído. É o próximo item a endurecer.
</div>

<div class="quebra"></div>
<h2>6. A forma da não linearidade</h2>
<p>Esta era a análise nº 1 da lista de próximos passos, e foi feita. A pergunta:
<b>os efeitos das mutações se somam?</b></p>
<p>Ajustamos um modelo que supõe exatamente isso — que o efeito de uma combinação é a
soma dos efeitos individuais — e comparamos a previsão dele com o que foi medido.
<b>Se os efeitos somassem, os pontos cairiam sobre a diagonal.</b></p>

<figure>{img(F / 'fig6_curva_aditiva.png')}
<figcaption><b>Em 10 dos 12 conjuntos a curva é uma sigmoide: piso achatado,
transição íngreme, teto.</b> O piso é a região onde tudo já morreu e o modelo
continua prevendo valores menores sem que o medido desça. O teto é saturação.
</figcaption></figure>

<p><b>Por que isso importa para quem vai modelar.</b> A não linearidade não é um
detalhe: é a maior parte do desvio em relação ao modelo aditivo. E ela tem duas
pontas — piso e teto — o que significa que uma transformação logarítmica <i>não</i>
resolve, porque log comprime só a ponta de cima.</p>

<p>Duas exceções valem nota. <b>Phototropin</b> é quase linear: ali os efeitos
realmente se somam. <b>TrpB</b> entorta para o outro lado, com retornos
decrescentes.</p>

<figure>{img(F / 'fig7_assimetria.png')}
<figcaption><b>O tipo de erro que o modelo aditivo comete separa os conjuntos em dois
grupos.</b> Quando acerta a ordem e erra a escala, falta uma transformação. Quando
erra a ordem — TrpB, NucB, ParD3, IGP — nenhuma transformação resolve: há interação
entre as mutações.</figcaption></figure>

<div class="caixa">
<b>Para entender a figura acima.</b> Pearson mede se os valores batem; Spearman mede
se a <i>ordem</i> bate. Uma transformação que não altera a ordem (esticar, comprimir,
curvar sem cruzar) muda o Pearson e deixa o Spearman intacto. Então: ponto escuro à
direita significa "a ordem está certa, só a escala está errada". Ponto escuro à
esquerda significa "a ordem está errada" — e isso <b>nenhuma</b> transformação
conserta.
</div>

<div class="caixa alerta">
<b>Consequência direta para a nossa pergunta.</b> O piso é o obstáculo. Numa faixa
onde todas as variantes estão mortas, não dá para distinguir "as duas mutações se
compensaram em parte" de "as duas mataram a proteína". <b>Candidatos compensatórios
que caem na faixa do piso não são interpretáveis</b> — o que estreita ainda mais os
0,73%.
</div>

<p class="sub">Ressalva: "sigmoide" aqui é descrição visual, não ajuste. Nenhuma
função sigmoidal foi ajustada nem comparada com alternativas. Detalhes em
<code>exploratoria/RESULTADO_ANALISE1.md</code>.</p>

<div class="rodape">
<b>Como foi feito.</b> Estatísticas calculadas sobre os dados completos (375 MB, 12
arquivos), exceto a consistência sequência/mutação, que usa amostras estratificadas
por ordem mutacional (semente 20261126). Dados brutos abertos somente para leitura.
Python 3.12.10. Perfilamento genérico com a skill <i>exploratory-data-analysis</i>
(K-Dense, MIT); figuras seguindo a skill <i>dataviz</i>, paleta de referência
validada. Código em <code>exploratoria/src/</code>, tabelas em
<code>exploratoria/resultados/</code>.<br><br>
<b>Citação exigida pela licença da skill</b>, caso contribua para manuscrito: Kassis,
T., Agarwal, V., He, Y., Patel, D., &amp; Brueckner, A. M. (2026). <i>Scientific Agent
Skills: A Library of Procedural Knowledge for Research Agents.</i> arXiv:2609.00065.
</div>

</body></html>"""

    out = Path(args.out)
    htm = out.with_suffix(".html")
    htm.write_text(html, encoding="utf-8")
    print(f"  HTML: {htm}  ({htm.stat().st_size / 1024:.0f} KB)")

    cmd = [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
           "--no-pdf-header-footer", f"--print-to-pdf={out.resolve()}",
           htm.resolve().as_uri()]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if out.exists():
        print(f"  PDF:  {out}  ({out.stat().st_size / 1024:.0f} KB)")
    else:
        print("  FALHA ao gerar PDF")
        print((r.stderr or "")[:600])


if __name__ == "__main__":
    main()
