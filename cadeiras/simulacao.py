"""Distribuição de cadeiras de Deputado Federal 2026 (TSE): cenário A (federações atuais)
cenário B (PT, PCdoB, PV, PSB, PSOL, Rede e PDT como uma única federação por UF)
e cenário C (apenas PT, PCdoB, PV, PSOL e Rede em federação única por UF; PSB e PDT isolados).

Uso: python3 -I simulacao.py <dir_partido_munzona> <dir_candidato_munzona> <dir_saida>
"""
import csv
import glob
import math
import os
import sys
from collections import defaultdict

CADEIRAS = {
    'SP': 70, 'MG': 53, 'RJ': 46, 'BA': 39, 'RS': 31, 'PR': 30, 'PE': 25, 'CE': 22,
    'MA': 18, 'GO': 17, 'PA': 17, 'SC': 16, 'PB': 12, 'ES': 10, 'PI': 10, 'AL': 9,
    'AM': 8, 'MT': 8, 'MS': 8, 'RN': 8, 'RO': 8, 'SE': 8, 'AC': 8, 'AP': 8, 'DF': 8,
    'RR': 8, 'TO': 8,
}
BLOCO_B = {'PT', 'PCDOB', 'PV', 'PSB', 'PSOL', 'REDE', 'PDT'}
NOME_B = 'BLOCO B (PT/PCdoB/PV/PSB/PSOL/REDE/PDT)'
BLOCO_C = {'PT', 'PCDOB', 'PV', 'PSOL', 'REDE'}      # cenário C: só estes cinco se federam; PSB e PDT seguem isolados
NOME_C = 'FEDERACAO C (PT/PCdoB/PV/PSOL/REDE)'


def ler(path):
    with open(path, encoding='latin1', newline='') as f:
        yield from csv.DictReader(f, delimiter=';')


def carregar(dir_part, dir_cand):
    """Retorna, por UF: votos de legenda por partido, candidatos e entidade atual (A) de cada partido."""
    leg = defaultdict(lambda: defaultdict(int))      # uf -> partido -> votos de legenda válidos
    ent_a = defaultdict(dict)                        # uf -> partido -> entidade (federação ou partido)
    for uf in CADEIRAS:
        for r in ler(f'{dir_part}/votacao_partido_munzona_2026_{uf}.csv'):
            if r['CD_CARGO'] != '6':
                continue
            p = r['SG_PARTIDO']
            leg[uf][p] += int(r['QT_TOTAL_VOTOS_LEG_VALIDOS'])
            ent_a[uf][p] = r['SG_FEDERACAO'] if r['TP_AGREMIACAO'] == 'Federação' else p
    cands = defaultdict(lambda: defaultdict(lambda: {'v': 0}))  # uf -> sq -> dados
    for uf in CADEIRAS:
        for r in ler(f'{dir_cand}/votacao_candidato_munzona_2026_{uf}.csv'):
            if r['CD_CARGO'] != '6':
                continue
            c = cands[uf][r['SQ_CANDIDATO']]
            c['v'] += int(r['QT_VOTOS_NOMINAIS_VALIDOS'])
            c['partido'] = r['SG_PARTIDO']
            c['nome'] = r['NM_URNA_CANDIDATO']
            c['oficial'] = r['DS_SIT_TOT_TURNO']
    return leg, cands, ent_a


def distribuir(uf, vagas, leg, cands, mapa, qe_fixo=None):
    """mapa: partido -> entidade. Retorna (qe, {entidade: dict}, lista de eleitos)."""
    ent = defaultdict(lambda: {'leg': 0, 'nom': 0, 'cands': []})
    for p, v in leg.items():
        ent[mapa[p]]['leg'] += v
    for sq, c in cands.items():
        e = ent[mapa[c['partido']]]
        e['nom'] += c['v']
        e['cands'].append((c['v'], sq))
    for e in ent.values():
        e['votos'] = e['leg'] + e['nom']
        e['cands'].sort(key=lambda t: (-t[0], t[1]))
        e['n'] = 0          # cadeiras
        e['i'] = 0          # ponteiro na lista ordenada
        e['qp'] = e['s1'] = e['s2'] = 0
    validos = sum(e['votos'] for e in ent.values())
    qe = validos / vagas
    qe = math.floor(qe) + (1 if qe - math.floor(qe) > 0.5 else 0)   # art. 106
    if qe_fixo is not None:
        qe = qe_fixo
    min10, min20 = 0.10 * qe, 0.20 * qe
    eleitos = []

    def proximo(e, minimo):
        """Próximo candidato não eleito com votos >= minimo (lista ordenada; só o topo importa)."""
        if e['i'] < len(e['cands']) and e['cands'][e['i']][0] >= minimo and e['cands'][e['i']][0] > 0:
            return e['cands'][e['i']]
        return None

    def eleger(nome, e, fase):
        v, sq = e['cands'][e['i']]
        e['i'] += 1
        e['n'] += 1
        e[fase] += 1
        eleitos.append((nome, sq, fase, v))

    # 1) quociente partidário (art. 107), limitado pela barreira de 10% do QE
    for nome, e in ent.items():
        qp = int(e['votos'] // qe)
        for _ in range(qp):
            if not proximo(e, min10):
                break
            eleger(nome, e, 'qp')
    restantes = vagas - len(eleitos)
    # 2) sobras, rodada 1: >=80% QE e candidato >=20% QE (art. 109)
    while restantes > 0:
        el = [(e['votos'] / (e['n'] + 1), nome) for nome, e in ent.items()
              if e['votos'] >= 0.8 * qe and proximo(e, min20)]
        if not el:
            break
        _, nome = max(el, key=lambda t: (t[0], ent[t[1]]['cands'][ent[t[1]]['i']][0]))
        eleger(nome, ent[nome], 's1')
        restantes -= 1
    # 3) sobras, rodada 2 (STF): todas as entidades com candidato disponível, maiores médias
    while restantes > 0:
        el = [(e['votos'] / (e['n'] + 1), nome) for nome, e in ent.items() if proximo(e, 1)]
        _, nome = max(el, key=lambda t: (t[0], ent[t[1]]['cands'][ent[t[1]]['i']][0]))
        eleger(nome, ent[nome], 's2')
        restantes -= 1
    return qe, validos, ent, eleitos


def main(dir_part, dir_cand, saida):
    os.makedirs(saida, exist_ok=True)
    leg, cands, ent_a = carregar(dir_part, dir_cand)
    res = {'A': {}, 'B': {}, 'C': {}}
    comparacao = []
    for uf, vagas in CADEIRAS.items():
        mapa_a = ent_a[uf]
        mapa_b = {p: (NOME_B if p in BLOCO_B else e) for p, e in mapa_a.items()}
        # partidos com candidatos mas sem linha de legenda: erro explícito
        for c in cands[uf].values():
            assert c['partido'] in mapa_a, (uf, c['partido'])
        mapa_c = {p: (NOME_C if p in BLOCO_C else e) for p, e in mapa_a.items()}
        for cen, mapa in (('A', mapa_a), ('B', mapa_b), ('C', mapa_c)):
            res[cen][uf] = distribuir(uf, vagas, leg[uf], cands[uf], mapa)
        # validação do cenário A contra o resultado oficial do TSE
        mine = {sq for _, sq, _, _ in res['A'][uf][3]}
        off = {sq for sq, c in cands[uf].items() if c['oficial'].startswith('ELEITO')}
        comparacao.append((uf, len(mine), len(off), sorted(mine - off), sorted(off - mine)))

    # saídas
    with open(f'{saida}/cadeiras_por_uf_entidade.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['cenario', 'uf', 'entidade', 'votos', 'cadeiras', 'qp', 'sobras1', 'sobras2', 'qe'])
        for cen in 'ABC':
            for uf in CADEIRAS:
                qe, _, ent, _ = res[cen][uf]
                for n, e in sorted(ent.items()):
                    if e['votos']:
                        w.writerow([cen, uf, n, e['votos'], e['n'], e['qp'], e['s1'], e['s2'], qe])
    for cen in 'ABC':
        with open(f'{saida}/eleitos_cenario_{cen}.csv', 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['uf', 'entidade', 'candidato', 'sq', 'partido', 'fase', 'votos'])
            for uf in CADEIRAS:
                for nome, sq, fase, v in res[cen][uf][3]:
                    c = cands[uf][sq]
                    w.writerow([uf, nome, c['nome'], sq, c['partido'], fase, v])
    with open(f'{saida}/validacao_cenario_A.txt', 'w') as f:
        for uf, a, b, x, y in comparacao:
            f.write(f'{uf} meu={a} oficial={b} so_meu={x} so_oficial={y}\n')
    return res, comparacao, cands


if __name__ == '__main__':
    main(*sys.argv[1:4])
