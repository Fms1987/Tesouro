"""Relatório em padrão ABNT (NBR 14724, 6024, 6028, 6023, 10520; tabulação conforme IBGE) a partir de resultados/.

Uso: python3 gerar_relatorio_abnt.py   (executar dentro de cadeiras/)
"""
import colorsys
import math

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

R = 'resultados/'
SAIDA = R + 'relatorio_abnt_cadeiras_2026.pdf'
FONTE = 'Times-Roman'
FONTE_B = 'Times-Bold'
FONTE_I = 'Times-Italic'
LARG = A4[0] - 5 * cm      # margens: esquerda 3, direita 2

# ---------------------------------------------------------------- dados
d = pd.read_csv(R + 'cadeiras_por_uf_entidade.csv')
eA = pd.read_csv(R + 'eleitos_cenario_A.csv')
eB = pd.read_csv(R + 'eleitos_cenario_B.csv')
fal = pd.read_csv(R + 'votos_faltantes_mais_uma_cadeira.csv')
perdas = pd.read_csv(R + 'perdas_cenario_B.csv')

SETE = ['PT/PC do B/PV', 'PSOL/REDE', 'PSB', 'PDT']
# Classificação de Bolognesi, Ribeiro, Codato e Silva (2025), Opinião Pública 31, e31120, Tabela 1: média ponderada de 2022
# (escala 0 a 10) e categoria. Ordem esquerda-direita pela média ponderada. Limiares: 0 a 1,5 extrema-esquerda; 1,51 a 3
# esquerda; 3,01 a 4,49 centro-esquerda; 4,5 a 5,5 centro; 5,51 a 7 centro-direita; 7,01 a 8,5 direita; 8,51 a 10 extrema-direita.
EXE, ESQ, CEE, CEN, CED, DIR, EXD, NC = ('Extrema-esquerda', 'Esquerda', 'Centro-esquerda', 'Centro', 'Centro-direita',
                                         'Direita', 'Extrema-direita', 'Não classificado')
GRUPOS = (EXE, ESQ, CEE, CEN, CED, DIR, EXD, NC)
LIMIARES = [(1.5, EXE), (3.0, ESQ), (4.49, CEE), (5.5, CEN), (7.0, CED), (8.5, DIR), (10.0, EXD)]


def categoria(m):
    return next(g for lim, g in LIMIARES if m <= lim)


# (partido 2026, sigla no estudo, média ponderada 2022). PRD: média de PTB (7,955) e Patriota (8,862), regra de fusão dos autores.
BRUTO = [('PSOL', 'PSOL', 1.453), ('PCDOB', 'PCdoB', 1.834), ('PT', 'PT', 2.761), ('PSB', 'PSB', 3.699),
         ('REDE', 'REDE', 3.802), ('PDT', 'PDT', 3.977), ('PV', 'PV', 4.245), ('SOLIDARIEDADE', 'SDD', 6.193),
         ('CIDADANIA', 'CDD', 6.358), ('AVANTE', 'AVANTE', 6.667), ('MDB', 'MDB', 6.698), ('PSDB', 'PSDB', 6.966),
         ('PSD', 'PSD', 7.151), ('PODE', 'PODE', 7.666), ('PP', 'PROGRE', 8.398),
         ('PRD', 'PTB e PATRI (média)', round((7.955 + 8.862) / 2, 3)), ('REPUBLICANOS', 'REP', 8.584),
         ('UNIÃO', 'UNIAO', 8.749), ('NOVO', 'NOVO', 8.934), ('PL', 'PL', 9.068), ('MISSÃO', 'sem correspondente', None)]
assert [m for _, _, m in BRUTO if m] == sorted(m for _, _, m in BRUTO if m)
ORDEM = [(p, categoria(m) if m is not None else NC, sg, m) for p, sg, m in BRUTO]
GRUPO = {p: g for p, g, _, _ in ORDEM}
MEDIA = {p: m for p, _, _, m in ORDEM}
NOME = {'PCDOB': 'PCdoB', 'REDE': 'Rede', 'UNIÃO': 'União', 'MISSÃO': 'Missão', 'SOLIDARIEDADE': 'Solidariedade',
        'REPUBLICANOS': 'Republicanos', 'AVANTE': 'Avante', 'PODE': 'Podemos', 'NOVO': 'Novo', 'CIDADANIA': 'Cidadania'}
nome = lambda p: NOME.get(p, p)
cA = eA.groupby('partido').size().to_dict()
cB = eB.groupby('partido').size().to_dict()
assert sum(cA.values()) == 513 and sum(cB.values()) == 513
assert set(cA) | set(cB) <= {p for p, _, _, _ in ORDEM}, (set(cA) | set(cB)) - {p for p, _, _, _ in ORDEM}
# Conferência das categorias com a coluna "Ideologia categórica" da Tabela 1 do artigo.
_ESPERADO = {'PSOL': EXE, 'PCDOB': ESQ, 'PT': ESQ, 'PSB': CEE, 'REDE': CEE, 'PDT': CEE, 'PV': CEE, 'SOLIDARIEDADE': CED,
             'CIDADANIA': CED, 'AVANTE': CED, 'MDB': CED, 'PSDB': CED, 'PSD': DIR, 'PODE': DIR, 'PP': DIR,
             'REPUBLICANOS': EXD, 'UNIÃO': EXD, 'NOVO': EXD, 'PL': EXD}
assert all(GRUPO[p] == g for p, g in _ESPERADO.items()), [(p, GRUPO[p], g) for p, g in _ESPERADO.items() if GRUPO[p] != g]


def gerar_cores():
    cores = {}
    cfg = {EXE: (0.0, 0.0, 0.26, 0.26), ESQ: (0.0, 0.0, 0.42, 0.55), CEE: (0.07, 0.07, 0.48, 0.64),
           CEN: (0.15, 0.15, 0.50, 0.50), CED: (0.53, 0.53, 0.42, 0.68), DIR: (0.60, 0.60, 0.40, 0.56),
           EXD: (0.66, 0.66, 0.20, 0.36)}
    for g, (h0, h1, l0, l1) in cfg.items():
        membros = [p for p, gg, _, _ in ORDEM if gg == g]
        for i, p in enumerate(membros):
            t = i / max(1, len(membros) - 1)
            r, gg_, b = colorsys.hls_to_rgb(h0 + (h1 - h0) * t, l0 + (l1 - l0) * t, 0.78)
            cores[p] = colors.Color(r, gg_, b)
    for p in [p for p, g, _, _ in ORDEM if g == NC]:
        cores[p] = colors.Color(0.6, 0.6, 0.6)
    return cores


CORES = gerar_cores()


def fmt(n):
    return f'{int(n):,}'.replace(',', '.')


ENT = {'PT/PC do B/PV': 'PT/PCdoB/PV', 'PSOL/REDE': 'PSOL/Rede', 'UNIÃO/PP': 'União/PP',
       'PSDB/CIDADANIA': 'PSDB/Cidadania', 'PRD/SOLIDARIEDADE': 'PRD/Solidariedade', 'REPUBLICANOS': 'Republicanos',
       'AVANTE': 'Avante', 'PODE': 'Podemos', 'MISSÃO': 'Missão', 'NOVO': 'Novo', 'CIDADANIA': 'Cidadania'}
ent = lambda n: ENT.get(n, n)


def sgn(n):
    return '0' if n == 0 else f'{int(n):+d}'


# ---------------------------------------------------------------- estilos (NBR 14724)
def est(nm, **kw):
    base = dict(fontName=FONTE, fontSize=12, leading=18, alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(nm, **base)


CORPO = est('Corpo', firstLineIndent=1.25 * cm)
CORPO0 = est('Corpo0')
H1 = est('H1', fontName=FONTE_B, alignment=TA_LEFT, spaceBefore=18, spaceAfter=18, keepWithNext=1)
H2 = est('H2', fontName=FONTE_B, alignment=TA_LEFT, spaceBefore=18, spaceAfter=18, keepWithNext=1)
HU = est('HU', fontName=FONTE_B, alignment=TA_CENTER, spaceAfter=18)          # títulos sem indicativo numérico
HUS = est('HUS', fontName=FONTE_B, alignment=TA_CENTER, spaceAfter=18)        # sumário, listas (fora do sumário)
CAP = est('Cap', fontSize=10, leading=12, alignment=TA_LEFT, spaceBefore=12, spaceAfter=4, keepWithNext=1)
CAPT = est('CapTabela', parent=None, fontSize=10, leading=12, alignment=TA_LEFT, spaceBefore=12, spaceAfter=4, keepWithNext=1)
CAPF = est('CapFigura', fontSize=10, leading=12, alignment=TA_LEFT, spaceBefore=12, spaceAfter=4, keepWithNext=1)
CAPQ = est('CapQuadro', fontSize=10, leading=12, alignment=TA_LEFT, spaceBefore=12, spaceAfter=4, keepWithNext=1)
FTE = est('Fonte', fontSize=10, leading=12, alignment=TA_LEFT, spaceBefore=3, spaceAfter=12)
CEL = est('Cel', fontSize=9, leading=10.5, alignment=TA_LEFT)
CELB = est('CelB', fontName=FONTE_B, fontSize=9, leading=10.5, alignment=TA_LEFT)
RES = est('Res', leading=12, firstLineIndent=0)                               # resumo: espaçamento simples
REF = est('Ref', leading=12, alignment=TA_LEFT, spaceAfter=12)
CENT = est('Cent', alignment=TA_CENTER, leading=18)
CENTB = est('CentB', alignment=TA_CENTER, fontName=FONTE_B, leading=18)
NAT = est('Nat', fontSize=10, leading=12, leftIndent=8 * cm, alignment=TA_JUSTIFY)
TOC1 = ParagraphStyle('toc1', fontName=FONTE_B, fontSize=12, leading=18, leftIndent=0, rightIndent=20)
TOC2 = ParagraphStyle('toc2', fontName=FONTE, fontSize=12, leading=18, leftIndent=0, rightIndent=20)
LST = ParagraphStyle('lst', fontName=FONTE, fontSize=12, leading=18, leftIndent=0, rightIndent=20)


class TOCk(TableOfContents):
    """Sumário/lista que escuta um tipo próprio de notificação."""

    def __init__(self, kind, **kw):
        super().__init__(**kw)
        self.kind = kind

    def notify(self, kind, stuff):
        if kind == self.kind:
            self.addEntry(*stuff)


class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if not isinstance(f, Paragraph):
            return
        sn = f.style.name
        txt = f.getPlainText()
        if sn in ('H1', 'H2', 'HU'):
            lvl = {'H1': 0, 'HU': 0, 'H2': 1}[sn]
            key = f'h{abs(hash(txt)) % 10**9}'
            self.canv.bookmarkPage(key)
            self.notify('TOCEntry', (lvl, txt, self.page, key))
        elif sn in ('CapTabela', 'CapFigura', 'CapQuadro'):
            key = f'c{abs(hash(txt)) % 10**9}'
            self.canv.bookmarkPage(key)
            self.notify({'CapTabela': 'LT', 'CapFigura': 'LF', 'CapQuadro': 'LQ'}[sn], (0, txt, self.page, key))


# ---------------------------------------------------------------- tabelas (IBGE/NBR 14724) e quadros
def tabela(dados, cols, esq=(0,), fonte=9, cab_linhas=1, total_ultima=False):
    """Tabela aberta nas laterais (IBGE/NBR 14724). Colunas em `esq` alinhadas à esquerda, demais à direita."""
    out = []
    for i, row in enumerate(dados):
        negrito = i < cab_linhas or (total_ultima and i == len(dados) - 1)
        linha = []
        for j, c in enumerate(row):
            sty = ParagraphStyle(f'c{int(negrito)}{int(j in esq)}', fontName=FONTE_B if negrito else FONTE,
                                 fontSize=fonte, leading=fonte + 1.5, alignment=0 if j in esq else 2)
            linha.append(Paragraph(str(c), sty))
        out.append(linha)
    t = Table(out, colWidths=cols, repeatRows=cab_linhas)
    s = [('LINEABOVE', (0, 0), (-1, 0), 1.0, colors.black),
         ('LINEBELOW', (0, cab_linhas - 1), (-1, cab_linhas - 1), 0.5, colors.black),
         ('LINEBELOW', (0, -1), (-1, -1), 1.0, colors.black),
         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
         ('TOPPADDING', (0, 0), (-1, -1), 1.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
         ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3)]
    if total_ultima:
        s.append(('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black))
    t.setStyle(TableStyle(s))
    return t


def quadro(dados, cols, fonte=9):
    """Quadro: fechado lateralmente (NBR 14724)."""
    st = ParagraphStyle('q', fontName=FONTE, fontSize=fonte, leading=fonte + 1.5)
    sb = ParagraphStyle('qb', fontName=FONTE_B, fontSize=fonte, leading=fonte + 1.5)
    out = [[Paragraph(str(c), sb if i == 0 else st) for c in row] for i, row in enumerate(dados)]
    t = Table(out, colWidths=cols, repeatRows=1)
    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('TOPPADDING', (0, 0), (-1, -1), 1.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5)]))
    return t


contadores = {'T': 0, 'F': 0, 'Q': 0}


def legenda(tipo, titulo):
    contadores[tipo] += 1
    n = contadores[tipo]
    rot, est_ = {'T': ('Tabela', CAPT), 'F': ('Figura', CAPF), 'Q': ('Quadro', CAPQ)}[tipo]
    return Paragraph(f'<b>{rot} {n}.</b> {titulo}', est_)


def fonte(txt='Elaborada pelo autor com base em TSE (2026).'):
    return Paragraph(f'Fonte: {txt}', FTE)


# ---------------------------------------------------------------- hemiciclo
class Hemiciclo(Flowable):
    """Hemiciclo: um ponto por parlamentar, partidos em ordem esquerda-direita."""

    def __init__(self, contagem, largura=LARG, linhas=11):
        super().__init__()
        self.cont = [(p, contagem.get(p, 0)) for p, _, _, _ in ORDEM if contagem.get(p, 0) > 0]
        self.w = largura
        self.rows = linhas
        self.Rext = largura / 2 - 0.3 * cm
        self.hemi_h = self.Rext + 0.4 * cm
        self.grupos = [g for g in GRUPOS if any(GRUPO[p] == g for p, _ in self.cont)]
        self.leg_h = len(self.grupos) * 13 + 10
        self.height = self.hemi_h + self.leg_h
        self.width = largura

    def wrap(self, aw, ah):
        return self.width, self.height

    def posicoes(self, N):
        r0 = 0.38 * self.Rext
        radii = [r0 + i * (self.Rext - r0) / (self.rows - 1) for i in range(self.rows)]
        soma = sum(radii)
        n = [round(N * r / soma) for r in radii]
        n[-1] += N - sum(n)
        pos = []
        for r, k in zip(radii, n):
            for j in range(k):
                th = math.pi * (1 - j / (k - 1))
                pos.append((th, r))
        pos.sort(key=lambda t: (-round(t[0], 9), t[1]))
        gap = (self.Rext - r0) / (self.rows - 1)
        arc = min(math.pi * r / (k - 1) for r, k in zip(radii, n))
        return pos, 0.46 * min(gap, arc)

    def draw(self):
        c = self.canv
        N = sum(k for _, k in self.cont)
        pos, rad = self.posicoes(N)
        cx, cy = self.w / 2, self.leg_h + 0.2 * cm
        i = 0
        for p, k in self.cont:
            c.setFillColor(CORES[p])
            c.setStrokeColor(CORES[p])
            for _ in range(k):
                th, r = pos[i]
                c.circle(cx + r * math.cos(th), cy + r * math.sin(th), rad, stroke=0, fill=1)
                i += 1
        c.setFillColor(colors.black)
        c.setFont(FONTE_B, 20)
        c.drawCentredString(cx, cy + 14, str(N))
        c.setFont(FONTE, 9)
        c.drawCentredString(cx, cy + 3, 'deputados federais')
        # legenda: uma linha por categoria (Bolognesi et al., 2025), na ordem esquerda-direita
        for lin, g in enumerate(self.grupos):
            membros = [(p, k) for p, k in self.cont if GRUPO[p] == g]
            y = self.leg_h - 10 - lin * 13
            c.setFillColor(colors.black)
            c.setFont(FONTE_B, 8.5)
            c.drawString(0, y, f'{g}: {sum(k for _, k in membros)}')
            x = 3.7 * cm
            for p, k in membros:
                c.setFillColor(CORES[p])
                c.circle(x + 4, y + 3, 4, stroke=0, fill=1)
                c.setFillColor(colors.black)
                c.setFont(FONTE, 8.5)
                t = f'{nome(p)} {k}'
                c.drawString(x + 12, y, t)
                x += 12 + stringWidth(t, FONTE, 8.5) + 10


# ---------------------------------------------------------------- conteúdo
S = []
tot_A = d[d.cenario == 'A'].groupby('entidade').cadeiras.sum()
tot_B = d[d.cenario == 'B'].groupby('entidade').cadeiras.sum()
a7 = int(tot_A[SETE].sum())
b7 = int(tot_B[[i for i in tot_B.index if i.startswith('BLOCO')]].sum())
assert (a7, b7) == (124, 143)
n_ufs_ganho = 0
a_uf = d[(d.cenario == 'A') & d.entidade.isin(SETE)].groupby('uf').cadeiras.sum()
b_uf = d[(d.cenario == 'B') & d.entidade.str.startswith('BLOCO')].groupby('uf').cadeiras.sum()
ganhos = (b_uf - a_uf.reindex(b_uf.index).fillna(0))
n_ufs_ganho = int((ganhos > 0).sum())
assert (ganhos >= 0).all()
perd_fora = perdas[~perdas.entidade.isin(SETE)]
n_perd = len(perd_fora)
assert n_perd == 19

TITULO = 'DISTRIBUIÇÃO DE CADEIRAS DE DEPUTADO FEDERAL EM 2026: FEDERAÇÕES VIGENTES E CENÁRIO DE FEDERAÇÃO ÚNICA DE SETE PARTIDOS'

# --- título (sem capa, resumo, listas ou sumário)
S += [Paragraph(f'<b>{TITULO}</b>', CENT), Spacer(1, 18)]

# --- 1 introdução
S += [Paragraph('1 INTRODUÇÃO', H1)]
S += [Paragraph('A eleição para a Câmara dos Deputados adota o sistema proporcional de lista aberta, com apuração separada em '
                'cada um dos 26 estados e no Distrito Federal (BRASIL, 1965). O número de cadeiras por unidade da federação é '
                'fixado em lei complementar, com mínimo de 8 e máximo de 70, e soma 513 (BRASIL, 1988; BRASIL, 1993). Partidos '
                'reunidos em federação partidária atuam como um único partido para fins de apuração, o que altera o cálculo do '
                'quociente partidário e das sobras.', CORPO),
      Paragraph('Este relatório compara dois cenários para a eleição de 2026. No cenário A, aplicam-se as federações '
                'efetivamente registradas. No cenário B, hipotético, os votos de PT, PSB, PSOL, PDT, PV, PCdoB e Rede são '
                'contabilizados como os de uma única federação em cada unidade da federação. O objetivo é medir quantas '
                'cadeiras o conjunto de partidos ocuparia em cada cenário, quais legendas cederiam cadeiras e quantos votos '
                'faltaram ao conjunto para obter uma cadeira adicional.', CORPO),
      Paragraph('As cadeiras de cada cenário são ainda representadas em hemiciclos, com os partidos classificados no espectro '
                'ideológico segundo a pesquisa com especialistas de Bolognesi et al. (2025).', CORPO),
      Paragraph('A análise é um exercício de simulação sobre resultados de uma eleição já realizada. Ela não considera alteração '
                'de comportamento de eleitores, de candidatos ou de partidos que decorreria de uma federação diferente, '
                'incluindo a própria definição das listas. Os resultados, portanto, medem o efeito aritmético da regra sobre '
                'votos observados.', CORPO),
      Paragraph('O texto organiza-se em quatro seções. A seção 2 descreve dados, regras e verificação. A seção 3 apresenta os '
                'resultados. A seção 4 reúne as considerações finais e as limitações.', CORPO)]

# --- 2 metodologia
S += [Paragraph('2 METODOLOGIA', H1), Paragraph('2.1 Dados', H2),
      Paragraph('Foram utilizados os arquivos de votação por partido e por candidato, por município e zona, das eleições '
                'gerais de 2026, publicados pelo Tribunal Superior Eleitoral (TSE, 2026), referentes ao cargo de deputado '
                'federal e ao primeiro turno. Os dados foram gerados em 11 de outubro de 2026, às 19h32. O total de votos '
                'válidos nominais e de legenda é de 113.678.019. Votos anulados sub judice não integram os votos válidos. '
                'Os votos nominais constantes dos dois arquivos coincidem em todas as combinações de unidade da federação e '
                'partido.', CORPO),
      Paragraph('2.2 Cenários', H2),
      Paragraph('O cenário A mantém as cinco federações vigentes: PT, PCdoB e PV; PSOL e Rede; PSDB e Cidadania; União e PP; '
                'PRD e Solidariedade. PSB e PDT concorrem isoladamente. No cenário B, os votos de legenda e nominais de PT, '
                'PCdoB, PV, PSB, PSOL, Rede e PDT são somados em uma única entidade, com lista única de candidatos em cada '
                'unidade da federação. O total de votos válidos e o número de cadeiras de cada unidade permanecem iguais, de '
                'modo que o quociente eleitoral não se altera entre os cenários.', CORPO),
      Paragraph('2.3 Regras de distribuição', H2),
      Paragraph('Aplicaram-se as regras do Código Eleitoral na redação da Lei nº 14.211/2021 (BRASIL, 1965; BRASIL, 2021), '
                'conforme a seguinte sequência: (a) quociente eleitoral, com arredondamento do art. 106; (b) quociente '
                'partidário, com desprezo de frações (art. 107), limitado pelo número de candidatos com votação nominal de '
                'pelo menos 10% do quociente eleitoral; (c) primeira rodada de sobras, por maiores médias, entre entidades '
                'com ao menos 80% do quociente eleitoral e candidato com ao menos 20% do quociente eleitoral; (d) segunda '
                'rodada, sem esses filtros, entre as entidades com candidato disponível, conforme a decisão do Supremo '
                'Tribunal Federal nas Ações Diretas de Inconstitucionalidade 7228, 7263 e 7311 (BRASIL, 2024), segundo a '
                'descrição fornecida pelo autor, sem conferência do inteiro teor do acórdão. Dentro de cada entidade, as '
                'cadeiras são ocupadas pelos candidatos em ordem decrescente de votação nominal.', CORPO),
      Paragraph('2.4 Verificação', H2),
      Paragraph('Três verificações foram realizadas. Primeira, o conjunto de candidatos eleitos calculado no cenário A foi '
                'comparado ao conjunto de eleitos informado pelo TSE em cada unidade da federação, sem divergência. Segunda, '
                'uma implementação independente, com aritmética de frações exatas e estruturas de dados distintas, '
                'reproduziu as cadeiras de 820 combinações de unidade da federação e entidade nos dois cenários. Terceira, '
                'para os votos faltantes, confirmou-se em cada unidade que o valor encontrado produz a cadeira adicional e '
                'que os 150 valores imediatamente inferiores, mais cerca de 60 pontos espaçados entre zero e o valor, não '
                'a produzem. Esta última verificação não passou por implementação independente.', CORPO),
      Paragraph('2.5 Votos faltantes', H2),
      Paragraph('Para cada unidade da federação, determinou-se o menor número de votos, de legenda mais nominais, que '
                'acrescentado ao próximo candidato não eleito do conjunto produz uma cadeira adicional, mantidos fixos o '
                'quociente eleitoral e os votos de todas as demais entidades. Os votos acrescentados não são retirados de '
                'outra entidade; se fossem transferidos da entidade que perderia a cadeira, o número necessário seria '
                'menor.', CORPO),
      Paragraph('2.6 Classificação ideológica e hemiciclo', H2),
      Paragraph('Para as figuras 1 e 2 e para a Tabela 3, os partidos foram posicionados segundo Bolognesi et al. (2025), '
                'que apresentam a classificação mais recente da literatura brasileira para todos os partidos. Os autores '
                'enviaram questionário online a 978 cientistas políticos cadastrados na Associação Brasileira de Ciência '
                'Política, com taxa de retorno de 48,8% em 2022, e pediram o posicionamento de cada partido em escala de onze '
                'pontos, de 0 (esquerda) a 10 (direita), em 2018 e em 2022. Utilizou-se a média ponderada de 2022 da Tabela 1 '
                'do artigo, na qual a média de 2022 é ajustada pela de 2018. A categoria de cada partido segue os limiares '
                'dos autores: de 0 a 1,5, extrema-esquerda; de 1,51 a 3, esquerda; de 3,01 a 4,49, centro-esquerda; de 4,5 a '
                '5,5, centro; de 5,51 a 7, centro-direita; de 7,01 a 8,5, direita; e de 8,51 a 10, extrema-direita. Os '
                'autores advertem que o termo "extrema" designa apenas a posição na escala e não qualifica o caráter '
                'antissistema do partido (BOLOGNESI et al., 2025).', CORPO),
      Paragraph('Duas legendas exigiram tratamento. O PRD, criado em 2023 pela fusão de PTB e Patriota, não consta do '
                'estudo; atribuiu-se a ele a média ponderada de PTB (7,955) e Patriota (8,862), regra que os próprios autores '
                'aplicam a partidos fundidos, de modo que o valor resultante, 8,409, é derivado e não publicado. O Missão '
                'não tem correspondente e permanece não classificado. A sigla "PROGRE" do estudo foi lida como Progressistas '
                '(PP). A classificação refere-se a 2022, e a posição dos partidos em 2026 pode ser diferente.', CORPO)]

ordq = [['Partido em 2026', 'Sigla no estudo', 'Média ponderada, 2022', 'Categoria']]
for p, g, sg, m in ORDEM:
    ordq.append([nome(p), sg, f'{m:.3f}'.replace('.', ',') if m is not None else 'sem dado', g])
S += [legenda('Q', 'Posição ideológica dos partidos em 2022, em ordem da esquerda para a direita'),
      quadro(ordq, [3.5 * cm, 4.5 * cm, 3.5 * cm, 4 * cm]),
      fonte('Elaborado pelo autor com base em Bolognesi et al. (2025, Tabela 1). Nota: PRD com valor derivado pela média '
            'de PTB e Patriota; escala de 0 (esquerda) a 10 (direita).')]

# --- 3 resultados
S += [Paragraph('3 RESULTADOS', H1), Paragraph('3.1 Cadeiras por entidade', H2),
      Paragraph(f'A Tabela 1 apresenta as cadeiras por entidade nos dois cenários. O conjunto de sete partidos passa de {a7} '
                f'cadeiras no cenário A para {b7} no cenário B, um acréscimo de {b7 - a7}. As demais variações são '
                f'negativas ou nulas e totalizam uma redução de {b7 - a7} cadeiras.', CORPO)]
t = pd.concat([tot_A.rename('A'), tot_B.rename('B')], axis=1).fillna(0).astype(int)
t = t[(t.A > 0) | (t.B > 0)].sort_values(['A', 'B'], ascending=False)
lin = [['Entidade', 'Cenário A', 'Cenário B', 'Variação']]
for n, r in t.iterrows():
    if n.startswith('BLOCO'):
        continue
    lin.append([ent(n), r.A, r.B, sgn(r.B - r.A)])
lin.append(['Federação única de sete partidos (cenário B)', 0, b7, sgn(b7)])
lin.append(['Total', int(t.A.sum()), int(t.B.sum()), '0'])
S += [legenda('T', 'Cadeiras por entidade, cenários A e B, Brasil, 2026'),
      tabela(lin, [7.5 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm], total_ultima=True),
      fonte('Elaborada pelo autor com base em TSE (2026). Nota: a variação refere-se à entidade, e a federação única '
            'do cenário B substitui PT/PCdoB/PV, PSB, PSOL/Rede e PDT.')]

S += [Paragraph('3.2 Cadeiras por partido', H2),
      Paragraph('A Tabela 2 desagrega as cadeiras por partido. Dentro de uma federação, as cadeiras são ocupadas pelos '
                'candidatos mais votados da lista conjunta, de modo que a distribuição entre os partidos do conjunto é '
                'consequência da votação individual e não de cota partidária. A Tabela 3 agrega as cadeiras por categoria ideológica e as figuras 1 e 2 apresentam os '
                'hemiciclos dos dois cenários.', CORPO)]
lin = [['Partido', 'Categoria (Bolognesi et al., 2025)', 'Média ponderada', 'Cenário A', 'Cenário B', 'Variação']]
for p, g, _, m in ORDEM:
    lin.append([nome(p), g, f'{m:.3f}'.replace('.', ',') if m is not None else 'sem dado', cA.get(p, 0), cB.get(p, 0), sgn(cB.get(p, 0) - cA.get(p, 0))])
lin.append(['Total', '', '', 513, 513, '0'])
S += [legenda('T', 'Cadeiras por partido, cenários A e B, Brasil, 2026'),
      tabela(lin, [3 * cm, 4.2 * cm, 2.4 * cm, 2 * cm, 2 * cm, 2.4 * cm], esq=(0, 1), total_ultima=True),
      fonte('Elaborada pelo autor com base em TSE (2026). Nota: partidos ordenados segundo o Quadro 1.')]
def soma_grupo(c, g):
    return sum(v for p, v in c.items() if GRUPO[p] == g)


lin = [['Categoria (Bolognesi et al., 2025)', 'Cenário A', '% A', 'Cenário B', '% B', 'Variação']]
for g in GRUPOS:
    a_, b_ = soma_grupo(cA, g), soma_grupo(cB, g)
    lin.append([g, a_, f'{100 * a_ / 513:.1f}'.replace('.', ','), b_, f'{100 * b_ / 513:.1f}'.replace('.', ','), sgn(b_ - a_)])
lin.append(['Total', 513, '100,0', 513, '100,0', '0'])
S += [legenda('T', 'Cadeiras por categoria ideológica, cenários A e B, Brasil, 2026'),
      tabela(lin, [5 * cm, 2.2 * cm, 1.8 * cm, 2.2 * cm, 1.8 * cm, 2 * cm], total_ultima=True),
      fonte('Elaborada pelo autor com base em TSE (2026) e Bolognesi et al. (2025). Nota: nenhum partido com cadeiras '
            'ocupa a categoria Centro; Missão, sem dado, é a única legenda não classificada.')]
esq3 = (EXE, ESQ, CEE)
gA = {g: soma_grupo(cA, g) for g in GRUPOS}
gB = {g: soma_grupo(cB, g) for g in GRUPOS}
eA3, eB3 = sum(gA[g] for g in esq3), sum(gB[g] for g in esq3)
assert (eA3, eB3) == (a7, b7)
S += [Paragraph((f'Os sete partidos do conjunto ocupam as três categorias à esquerda do centro (Tabela 3), e nenhum partido com '
                f'cadeiras situa-se na categoria Centro, o que acompanha o achado de desaparecimento do centro ideológico de '
                f'Bolognesi et al. (2025). As três categorias à esquerda somam {eA3} cadeiras ({f'{100 * eA3 / 513:.1f}'.replace('.', ',')}%) no cenário A e '
                f'{eB3} ({f'{100 * eB3 / 513:.1f}'.replace('.', ',')}%) no cenário B. A centro-direita passa de {gA[CED]} para {gB[CED]} '
                f'({sgn(gB[CED] - gA[CED])}), a direita de {gA[DIR]} para {gB[DIR]} ({sgn(gB[DIR] - gA[DIR])}) e a extrema-direita '
                f'de {gA[EXD]} para {gB[EXD]} ({sgn(gB[EXD] - gA[EXD])}). O Missão, não classificado, mantém {gA[NC]} cadeira.'
                ).replace('.', ',', 0), CORPO)]
S += [KeepTogether([legenda('F', 'Hemiciclo da Câmara dos Deputados, cenário A (federações vigentes), 2026'),
                    Hemiciclo(cA), fonte('Elaborada pelo autor com base em TSE (2026). Nota: cada ponto representa um '
                                         'deputado; partidos ordenados e agrupados conforme Bolognesi et al. (2025) e o Quadro 1; cinza indica partido sem classificação.')]),
      KeepTogether([legenda('F', 'Hemiciclo da Câmara dos Deputados, cenário B (federação única de sete partidos), 2026'),
                    Hemiciclo(cB), fonte('Elaborada pelo autor com base em TSE (2026). Nota: cada ponto representa um '
                                         'deputado; partidos ordenados e agrupados conforme Bolognesi et al. (2025) e o Quadro 1; cinza indica partido sem classificação.')])]

# 3.3 por UF
S += [Paragraph('3.3 Conjunto de sete partidos por unidade da federação', H2),
      Paragraph(f'O conjunto ganha cadeiras em {n_ufs_ganho} unidades da federação e não perde em nenhuma (Tabela 4). Os '
                f'maiores acréscimos ocorrem em São Paulo (+{int(ganhos["SP"])}), Ceará (+{int(ganhos["CE"])}) e Rio Grande do Sul '
                f'(+{int(ganhos["RS"])}). Em Alagoas, Amazonas, Rondônia, Roraima e Tocantins, o conjunto não elege deputado '
                f'em nenhum dos cenários.', CORPO)]
bB = eB[eB.entidade.str.startswith('BLOCO')]
pv = bB.pivot_table(index='uf', columns='partido', values='sq', aggfunc='count', fill_value=0)
cols_p = ['PT', 'PSB', 'PSOL', 'PCDOB', 'PDT', 'PV', 'REDE']
lin = [['UF'] + [nome(p) for p in cols_p] + ['Cenário B', 'Cenário A', 'Variação']]
for u in sorted(d.uf.unique()):
    g = lambda p: int(pv.loc[u, p]) if (u in pv.index and p in pv.columns) else 0
    bb, aa = int(b_uf.get(u, 0)), int(a_uf.get(u, 0))
    lin.append([u] + [g(p) for p in cols_p] + [bb, aa, sgn(bb - aa)])
lin.append(['Brasil'] + [int(bB[bB.partido == p].shape[0]) for p in cols_p] + [b7, a7, sgn(b7 - a7)])
S += [legenda('T', 'Cadeiras do conjunto de sete partidos por unidade da federação, por partido, cenário B, e total do cenário A, 2026'),
      tabela(lin, [1.5 * cm] + [1.25 * cm] * 7 + [1.8 * cm, 1.8 * cm, 1.8 * cm], total_ultima=True, fonte=8.5),
      fonte('Elaborada pelo autor com base em TSE (2026). Nota: colunas de partidos referem-se ao cenário B; o cenário A '
            'soma as entidades PT/PCdoB/PV, PSOL/Rede, PSB e PDT.')]

# 3.4 perdas
S += [Paragraph('3.4 Entidades que cedem cadeiras', H2),
      Paragraph(f'No cenário B, {n_perd} cadeiras deixam de ser ocupadas por entidades fora do conjunto, uma por entidade e '
                f'unidade da federação (Tabela 5). Os componentes do conjunto deixam de existir como entidades separadas, e '
                f'suas cadeiras passam à federação única.', CORPO)]
pf = perd_fora.sort_values(['uf', 'entidade'])
lin = [['UF', 'Entidade', 'Cenário A', 'Cenário B', 'Variação']] + [
    [r.uf, ent(r.entidade), int(r.cadeiras_A), int(r.cadeiras_B), sgn(r.delta)] for r in pf.itertuples()]
S += [legenda('T', 'Entidades externas ao conjunto que perdem cadeiras no cenário B, por unidade da federação, 2026'),
      tabela(lin, [2 * cm, 5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm], esq=(0, 1)),
      fonte('Elaborada pelo autor com base em TSE (2026).')]

# 3.5 faltantes
S += [Paragraph('3.5 Votos faltantes para uma cadeira adicional', H2),
      Paragraph('A Tabela 6 apresenta, por unidade da federação, os votos que faltaram ao conjunto para obter uma cadeira '
                'adicional, conforme o método da subseção 2.5. Em valores absolutos, os menores déficits estão em Rondônia, '
                'Mato Grosso do Sul, Roraima e Amapá. Em proporção aos votos do conjunto, os menores estão em Mato Grosso '
                'do Sul, Rio Grande do Sul, São Paulo, Minas Gerais e Bahia. Os maiores déficits absolutos estão no Rio Grande '
                'do Norte, no Espírito Santo, em São Paulo e no Rio de Janeiro.', CORPO)]
lin = [['UF', 'Cadeiras do conjunto', 'Votos do conjunto', 'Votos faltantes', '% dos votos do conjunto',
        'Próximo candidato (votos)', 'Entidade que perde a cadeira']]
for r in fal.itertuples():
    nm = ' '.join(w.lower() if w.lower() in ('de', 'da', 'do', 'dos', 'das', 'e') else w.capitalize() for w in r.proximo_candidato.split())
    lin.append([r.uf, r.cadeiras_bloco_B, fmt(r.votos_bloco), fmt(r.votos_faltantes),
                f'{r.pct_sobre_votos_bloco:.1f}'.replace('.', ','), f'{nm}, {r.partido} ({fmt(r.votos_do_candidato)})',
                ent(r.cadeira_tirada_de)])
tf = tabela(lin, [1.1 * cm, 1.8 * cm, 2.2 * cm, 2.0 * cm, 2.0 * cm, 4.6 * cm, 2.3 * cm], esq=(0, 5, 6), fonte=8.5)
# colunas de texto à esquerda
S += [legenda('T', 'Votos que faltaram ao conjunto de sete partidos para uma cadeira adicional, por unidade da federação, 2026'),
      tf, fonte('Elaborada pelo autor com base em TSE (2026). Nota: quociente eleitoral e votos das demais entidades '
                'mantidos fixos; ordenação do menor para o maior déficit absoluto.')]

# --- 4 considerações finais
S += [Paragraph('4 CONSIDERAÇÕES FINAIS', H1),
      Paragraph(f'Sob a regra simulada, a federação única de sete partidos teria {b7} cadeiras, contra {a7} somadas pelos '
                f'mesmos partidos nas federações vigentes, um acréscimo de {b7 - a7}. Este relatório não decompõe o ganho '
                f'entre quociente partidário e sobras. As {n_perd} cadeiras adicionais saem de União e PP, PSD, Republicanos, MDB, '
                f'Podemos, PL e Novo, conforme a Tabela 5.', CORPO),
      Paragraph('Limitações devem ser consideradas. Primeira, os dados são de 11 de outubro de 2026 e podem mudar com o '
                'julgamento de candidaturas sub judice. Segunda, a regra da segunda rodada de sobras segue a descrição do autor '
                'e não foi conferida com o inteiro teor do acórdão. Terceira, empates exatos de média ou de votação não '
                'foram verificados nem tratados por critério de idade. Quarta, o cenário B mantém os votos observados; uma '
                'federação diferente poderia alterar candidaturas, lista e votação. Quinta, os votos faltantes são uma '
                'medida de sensibilidade com acréscimo puro de votos. Sexta, a classificação ideológica de Bolognesi et al. (2025) '
                'refere-se a 2022, deriva de pesquisa com especialistas (978 convidados, 48,8% de retorno), não cobre o Missão e '
                'atribui ao PRD um valor derivado da média de PTB e Patriota; as categorias "extrema" indicam apenas posição '
                'na escala e não o caráter antissistema do partido.',
                CORPO),
      Paragraph('Recomenda-se, em trabalhos futuros, conferir o acórdão do STF, repetir o cálculo com os dados finais '
                'totalizados do TSE, tratar empates segundo o art. 110 do Código Eleitoral e estimar cenários em que os votos '
                'extras sejam transferidos de outras entidades, e não apenas acrescentados.', CORPO)]

# --- referências (NBR 6023)
refs = [
    'BOLOGNESI, Bruno; RIBEIRO, Ednaldo; CODATO, Adriano; SILVA, Bruno Fernando da. O desaparecimento do centro '
    'ideológico no sistema partidário brasileiro: a classificação mais atualizada dos experts. <b>Opinião Pública</b>, '
    'Campinas, v. 31, e31120, 2025. DOI: 10.1590/1807-0191202531120. Dados: https://doi.org/10.7910/DVN/MFIXKW. '
    'Disponível em: https://periodicos.sbu.unicamp.br/ojs/index.php/op/article/view/8682072. Acesso em: 13 out. 2026.',
    'BRASIL. <b>Constituição da República Federativa do Brasil de 1988</b>. Brasília, DF: Presidência da República, 1988. '
    'Art. 45.',
    'BRASIL. <b>Lei nº 4.737, de 15 de julho de 1965</b>. Institui o Código Eleitoral. Brasília, DF: Presidência da '
    'República, 1965.',
    'BRASIL. <b>Lei Complementar nº 78, de 30 de dezembro de 1993</b>. Disciplina a fixação do número de Deputados. '
    'Brasília, DF: Presidência da República, 1993.',
    'BRASIL. <b>Lei nº 14.211, de 1º de outubro de 2021</b>. Altera o Código Eleitoral quanto à distribuição das vagas '
    'nas eleições proporcionais. Brasília, DF: Presidência da República, 2021.',
    'BRASIL. Supremo Tribunal Federal. <b>Ações Diretas de Inconstitucionalidade 7228, 7263 e 7311</b>. Brasília, DF: STF, '
    '2024. Numeração e conteúdo conforme informado pelo autor, a conferir.',
    'TRIBUNAL SUPERIOR ELEITORAL (Brasil). <b>Resultados da votação por partido e por candidato em município e zona: '
    'eleições gerais 2026</b>. Brasília, DF: TSE, 2026. Disponível em: '
    'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_partido_munzona/votacao_partido_munzona_2026.zip e '
    'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2026.zip. '
    'Acesso em: 13 out. 2026.',
]
S += [Paragraph('REFERÊNCIAS', HU)] + [Paragraph(r, REF) for r in refs]

# ---------------------------------------------------------------- montagem
def num_pagina(c, doc):
    c.saveState()
    c.setFont(FONTE, 10)
    c.drawRightString(A4[0] - 2 * cm, A4[1] - 1.5 * cm, str(doc.page))
    c.restoreState()


doc = Doc(SAIDA, pagesize=A4, leftMargin=3 * cm, rightMargin=2 * cm, topMargin=3 * cm, bottomMargin=2 * cm,
          title='Distribuição de cadeiras de deputado federal em 2026')
frame = Frame(3 * cm, 2 * cm, LARG, A4[1] - 5 * cm, id='f', leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=num_pagina)])
doc.multiBuild(S)
