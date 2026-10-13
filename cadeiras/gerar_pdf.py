"""Gera o relatório PDF a partir dos CSVs em resultados/."""
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

R = 'resultados/'
d = pd.read_csv(R + 'cadeiras_por_uf_entidade.csv')
el = pd.read_csv(R + 'eleitos_cenario_B.csv')
fal = pd.read_csv(R + 'votos_faltantes_mais_uma_cadeira.csv')
perdas = pd.read_csv(R + 'perdas_cenario_B.csv')

st = getSampleStyleSheet()
H1 = ParagraphStyle('h1', parent=st['Heading1'], fontSize=14, spaceAfter=6, spaceBefore=10)
P = ParagraphStyle('p', parent=st['Normal'], fontSize=9, leading=12)
SM = ParagraphStyle('sm', parent=P, fontSize=8, leading=10, textColor=colors.HexColor('#444444'))
T = ParagraphStyle('t', parent=st['Title'], fontSize=18)


def fmt(n):
    return f'{int(n):,}'.replace(',', '.')


def tabela(dados, cols, header=1, zebra=True, align_right_from=1):
    t = Table(dados, colWidths=cols, repeatRows=header)
    sty = [('FONTSIZE', (0, 0), (-1, -1), 7.5), ('FONTNAME', (0, 0), (-1, header - 1), 'Helvetica-Bold'),
           ('BACKGROUND', (0, 0), (-1, header - 1), colors.HexColor('#1f3a5f')),
           ('TEXTCOLOR', (0, 0), (-1, header - 1), colors.white),
           ('ALIGN', (align_right_from, 0), (-1, -1), 'RIGHT'),
           ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#bbbbbb')),
           ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]
    if zebra:
        for i in range(header, len(dados)):
            if i % 2 == 0:
                sty.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f0f3f7')))
    t.setStyle(TableStyle(sty))
    return t


S = []
S += [Paragraph('Deputado Federal 2026: federações atuais vs. bloco B', T),
      Paragraph('Dados: TSE (votacao_partido_munzona e votacao_candidato_munzona 2026), geração de 11/10/2026 19:32. '
                'Total de votos válidos: 113.678.019. Total de cadeiras: 513.', SM), Spacer(1, 8)]

S += [Paragraph('1. Definição dos cenários', H1),
      Paragraph('<b>Cenário A (atual):</b> federações vigentes tratadas como partido único: PT/PCdoB/PV, PSOL/Rede, '
                'PSDB/Cidadania, UNIÃO/PP e PRD/Solidariedade. PSB e PDT concorrem isolados.', P),
      Paragraph('<b>Cenário B:</b> PT, PCdoB, PV, PSB, PSOL, Rede e PDT somam seus votos como uma única federação em cada UF. '
                'Votos válidos totais e número de cadeiras por UF não mudam, logo o quociente eleitoral (QE) é o mesmo.', P),
      Paragraph('<b>Regras aplicadas:</b> QE com arredondamento do art. 106 do CE; quociente partidário (art. 107) limitado '
                'por candidatos com no mínimo 10% do QE; sobras na 1ª rodada para entidades com 80% do QE e candidato com '
                '20% do QE (maiores médias, D\'Hondt); 2ª rodada sem filtros, conforme descrição das ADIs 7228, 7263 e 7311 '
                '(texto do acórdão não conferido). Votos anulados sub judice ficam fora.', P)]

# 2. Totais por entidade
t = d.pivot_table(index='entidade', columns='cenario', values='cadeiras', aggfunc='sum', fill_value=0)
t['dif'] = t.B - t.A
t = t.sort_values('A', ascending=False)
t = t[(t.A > 0) | (t.B > 0)]
linhas = [['Entidade', 'A', 'B', 'Dif.']]
for n, r in t.iterrows():
    nome = 'Bloco B (7 partidos)' if n.startswith('BLOCO') else n
    linhas.append([nome, int(r.A), int(r.B), (f'{int(r.dif):+d}' if r.dif else '0')])
sete = ['PT/PC do B/PV', 'PSOL/REDE', 'PSB', 'PDT']
a7 = int(t.loc[t.index.isin(sete), 'A'].sum()); b7 = int(t[t.index.str.startswith('BLOCO')].B.sum())
linhas.append(['Soma dos sete partidos', a7, b7, f'{b7 - a7:+d}'])
S += [Paragraph('2. Cadeiras por entidade (Brasil)', H1), tabela(linhas, [6 * cm, 2 * cm, 2 * cm, 2 * cm]),
      Spacer(1, 4), Paragraph('PSDB/Cidadania, PRD/Solidariedade, Avante e Missão não mudam.', SM)]

# 3. Por partido do bloco
oficial = {'PT': 70, 'PSB': 15, 'PSOL': 14, 'PCDOB': 11, 'PDT': 6, 'PV': 7, 'REDE': 1}
nomes = {'PT': 'PT', 'PSB': 'PSB', 'PSOL': 'PSOL', 'PCDOB': 'PCdoB', 'PDT': 'PDT', 'PV': 'PV', 'REDE': 'Rede'}
b = el[el.entidade.str.startswith('BLOCO')]
cnt = b.groupby('partido').size()
lin = [['Partido', 'A (oficial TSE)', 'B', 'Dif.']]
for p in ['PT', 'PSB', 'PSOL', 'PCDOB', 'PDT', 'PV', 'REDE']:
    lin.append([nomes[p], oficial[p], int(cnt[p]), (f'{int(cnt[p]) - oficial[p]:+d}' if int(cnt[p]) != oficial[p] else '0')])
lin.append(['Total', sum(oficial.values()), int(cnt.sum()), f'{int(cnt.sum()) - sum(oficial.values()):+d}'])
S += [Paragraph('3. Cadeiras por partido dentro do bloco B', H1), tabela(lin, [4 * cm, 3 * cm, 2 * cm, 2 * cm]),
      Spacer(1, 4), Paragraph('Dentro da federação, as cadeiras vão aos candidatos mais votados da lista única. '
                              'A divisão por partido é consequência, não cota.', SM)]
S.append(PageBreak())

# 4. por UF
pv = b.pivot_table(index='uf', columns='partido', values='sq', aggfunc='count', fill_value=0)
a_uf = d[(d.cenario == 'A') & d.entidade.isin(sete)].groupby('uf').cadeiras.sum()
b_uf = d[(d.cenario == 'B') & d.entidade.str.startswith('BLOCO')].groupby('uf').cadeiras.sum()
ufs = sorted(d.uf.unique())
lin = [['UF', 'PT', 'PSB', 'PSOL', 'PCdoB', 'PDT', 'PV', 'Rede', 'Bloco B', 'Hoje (A)', 'Dif.']]
for u in ufs:
    g = lambda p: int(pv.loc[u, p]) if (u in pv.index and p in pv.columns) else 0
    bb = int(b_uf.get(u, 0)); aa = int(a_uf.get(u, 0))
    lin.append([u, g('PT'), g('PSB'), g('PSOL'), g('PCDOB'), g('PDT'), g('PV'), g('REDE'), bb, aa, (f'{bb - aa:+d}' if bb != aa else '0')])
S += [Paragraph('4. Bloco B por UF e por partido', H1), tabela(lin, [1.3 * cm] + [1.5 * cm] * 10),
      Spacer(1, 4), Paragraph('Em AL, AM, RO, RR e TO o bloco não elege ninguém no cenário B. O bloco não perde cadeira em nenhuma UF.', SM)]
S.append(PageBreak())

# 5. perdas
p = perdas[~perdas.entidade.isin(sete)].sort_values(['uf', 'entidade'])
lin = [['UF', 'Entidade que perde', 'A', 'B']] + [[r.uf, r.entidade, int(r.cadeiras_A), int(r.cadeiras_B)] for r in p.itertuples()]
S += [Paragraph('5. Entidades que perdem cadeiras no cenário B (fora do bloco)', H1),
      tabela(lin, [1.5 * cm, 5 * cm, 1.5 * cm, 1.5 * cm]),
      Spacer(1, 4), Paragraph(f'Total: {len(p)} cadeiras, uma por entidade e UF. Os componentes do bloco (PT/PCdoB/PV, PSB, '
                              'PSOL/Rede, PDT) deixam de existir como entidades separadas e suas cadeiras passam à soma do bloco.', SM)]
S.append(PageBreak())

# 6. faltantes
lin = [['UF', 'Cad.\nbloco', 'Votos do\nbloco', 'QE', 'Votos\nfaltantes', '% do\nbloco', 'Próximo candidato (votos)', 'Perde a\ncadeira']]
for r in fal.itertuples():
    lin.append([r.uf, r.cadeiras_bloco_B, fmt(r.votos_bloco), fmt(r.qe), fmt(r.votos_faltantes),
                f'{r.pct_sobre_votos_bloco:.1f}'.replace('.', ',') + '%',
                f'{r.proximo_candidato.title()[:22]}, {r.partido} ({fmt(r.votos_do_candidato)})'.replace('Do ', 'do ').replace('De ', 'de '),
                r.cadeira_tirada_de])
S += [Paragraph('6. Votos que faltaram ao bloco B para ter mais uma cadeira, por UF', H1),
      Paragraph('Método: votos (legenda + nominais) acrescentados ao próximo candidato não eleito do bloco, com o QE e os votos '
                'de todos os demais mantidos fixos. Resultado: o menor acréscimo que, refazendo toda a distribuição, dá ao bloco '
                'uma cadeira a mais. Os votos extras não saem de ninguém; se viessem da entidade que perde a cadeira, o necessário seria menor. '
                'Ordenado do menor para o maior déficit.', P), Spacer(1, 4),
      tabela(lin, [0.9 * cm, 1.2 * cm, 2.1 * cm, 1.7 * cm, 1.9 * cm, 1.4 * cm, 5 * cm, 2.6 * cm], align_right_from=1)]
S.append(Spacer(1, 4))

S += [Paragraph('7. Verificações e limitações', H1),
      Paragraph('Votos nominais do arquivo por partido e do arquivo por candidato: zero divergências. '
                'Cenário A: os eleitos calculados coincidem com os eleitos oficiais do TSE nas 27 UFs (513 no total). '
                'Segunda implementação independente (frações exatas): zero divergências em 820 linhas (UF x entidade) nos cenários A e B. '
                'Votos faltantes: confirmado, em cada UF, que o valor encontrado dá uma cadeira a mais e que os 150 valores logo abaixo e cerca de 60 pontos '
                'espalhados abaixo dele não dão; este item não passou por segunda implementação.', P),
      Paragraph('Limitações: dados de 11/10/2026, sujeitos a mudanças de julgamento de candidaturas sub judice; regra da 2ª rodada de sobras '
                'segue a descrição fornecida, sem conferência do acórdão do STF; empates exatos de média ou de votos não foram checados nem '
                'tratados por idade do candidato. Código e CSVs em cadeiras/ (branch claude/cadeiras-federacao-2026).', P)]


def rodape(c, doc):
    c.setFont('Helvetica', 7); c.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f'Página {doc.page}')


SimpleDocTemplate('resultados/relatorio_cadeiras_2026.pdf', pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                  topMargin=1.5 * cm, bottomMargin=1.5 * cm, title='Deputado Federal 2026: federações vs bloco B'
                  ).build(S, onFirstPage=rodape, onLaterPages=rodape)
