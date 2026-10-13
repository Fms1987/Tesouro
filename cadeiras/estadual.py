"""Simulação dos cenários A, B e C para deputado estadual (cargo 7) em PE e AM.

Uso: python3 estadual.py <dir_partido_munzona> <dir_candidato_munzona>
Cadeiras de cada UF = número de eleitos oficiais no arquivo de candidatos.
"""
import sys

from simulacao import BLOCO_B, BLOCO_C, NOME_B, NOME_C, carregar, distribuir

UFS = ['PE', 'AM']
CENARIOS = {'A': (None, None), 'B': (BLOCO_B, NOME_B), 'C': (BLOCO_C, NOME_C)}


def main(dir_part, dir_cand):
    leg, cands, ent_a = carregar(dir_part, dir_cand, cargo='7', ufs=UFS)
    for uf in UFS:
        vagas = sum(1 for c in cands[uf].values() if c['oficial'].startswith('ELEITO'))
        print(f'\n===== {uf}: {vagas} cadeiras =====')
        res = {}
        for cen, (bloco, nome) in CENARIOS.items():
            mapa = {p: (nome if bloco and p in bloco else e) for p, e in ent_a[uf].items()}
            res[cen] = (mapa,) + distribuir(uf, vagas, leg[uf], cands[uf], mapa)
        qe, validos = res['A'][1], res['A'][2]
        mine = {sq for _, sq, _, _ in res['A'][4]}
        off = {sq for sq, c in cands[uf].items() if c['oficial'].startswith('ELEITO')}
        print(f'votos válidos {validos}, QE {qe}; A confere com oficial: {mine == off} ({len(mine)} vs {len(off)})')
        for cen in 'ABC':
            assert sum(e['n'] for e in res[cen][3].values()) == vagas
        ents = sorted({n for cen in 'ABC' for n, e in res[cen][3].items() if e['n']},
                      key=lambda n: -res['A'][3][n]['n'] if n in res['A'][3] else 0)
        print('entidade | votos | A | B | C')
        for n in ents:
            g = lambda c: res[c][3][n]['n'] if n in res[c][3] else 0
            v = max((res[c][3][n]['votos'] for c in 'ABC' if n in res[c][3]), default=0)
            print(f'{n} | {v} | {g("A")} | {g("B")} | {g("C")}')
        # por partido
        print('partido | A | B | C')
        cont = {c: {} for c in 'ABC'}
        for cen in 'ABC':
            for _, sq, _, _ in res[cen][4]:
                p = cands[uf][sq]['partido']
                cont[cen][p] = cont[cen].get(p, 0) + 1
        for p in sorted({p for c in cont.values() for p in c}, key=lambda p: -cont['A'].get(p, 0)):
            print(f'{p} | {cont["A"].get(p, 0)} | {cont["B"].get(p, 0)} | {cont["C"].get(p, 0)}')
        # votos faltantes
        for cen in 'BC':
            bloco, nome = CENARIOS[cen]
            mapa = res[cen][0]
            qe_c, _, ent0, _ = res[cen][1:]
            base = ent0[nome]['n']
            lista = ent0[nome]['cands']
            sq_prox, v_prox = lista[base][1], lista[base][0]

            def rodar(extra):
                c2 = {k: dict(v) for k, v in cands[uf].items()}
                c2[sq_prox]['v'] += extra
                return distribuir(uf, vagas, leg[uf], c2, mapa, qe_fixo=qe_c)[2]

            hi = 1
            while rodar(hi)[nome]['n'] <= base:
                hi *= 2
            lo = hi // 2
            while hi - lo > 1:
                mid = (lo + hi) // 2
                lo, hi = (lo, mid) if rodar(mid)[nome]['n'] > base else (mid, hi)
            assert rodar(hi)[nome]['n'] == base + 1 and rodar(hi - 1)[nome]['n'] == base
            e1 = rodar(hi)
            perde = [n for n in ent0 if n != nome and e1[n]['n'] < ent0[n]['n']]
            print(f'faltantes {cen}: bloco tem {base}, votos {ent0[nome]["votos"]}; faltam {hi} votos para {base + 1}; '
                  f'próximo {cands[uf][sq_prox]["nome"]} ({cands[uf][sq_prox]["partido"]}, {v_prox}); perde: {perde}')


if __name__ == '__main__':
    main(*sys.argv[1:3])
