"""Análises sobre o cenário B.

1) Votos adicionais (de legenda) que o bloco B precisa em cada UF para ganhar mais 1 cadeira.
2) Entidades que perdem cadeiras no cenário B, por UF.

Uso: python3 -I analise.py <dir_partido_munzona> <dir_candidato_munzona> <dir_saida>
"""
import csv
import os
import sys

from simulacao import BLOCO_B, CADEIRAS, NOME_B, carregar, distribuir


def mapas(ent_a):
    a = ent_a
    b = {p: (NOME_B if p in BLOCO_B else e) for p, e in a.items()}
    return a, b


def cadeiras_bloco(uf, leg, cands, mapa, extra):
    """Cadeiras do bloco B com `extra` votos de legenda adicionados ao bloco."""
    leg2 = dict(leg)
    leg2['PT'] = leg2.get('PT', 0) + extra
    qe, validos, ent, _ = distribuir(uf, CADEIRAS[uf], leg2, cands, mapa)
    return ent[NOME_B]['n'], qe, ent


def main(dir_part, dir_cand, saida):
    os.makedirs(saida, exist_ok=True)
    leg, cands, ent_a = carregar(dir_part, dir_cand)
    linhas = []
    for uf in CADEIRAS:
        _, mb = mapas(ent_a[uf])
        base, qe, ent = cadeiras_bloco(uf, leg[uf], cands[uf], mb, 0)
        votos = ent[NOME_B]['votos']
        # busca exponencial + bisseção do menor acréscimo que dá base+1 cadeiras
        hi = 1
        while cadeiras_bloco(uf, leg[uf], cands[uf], mb, hi)[0] <= base:
            hi *= 2
            if hi > 10_000_000:
                raise RuntimeError(uf)
        lo = hi // 2
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if cadeiras_bloco(uf, leg[uf], cands[uf], mb, mid)[0] > base:
                hi = mid
            else:
                lo = mid
        # verificação: hi dá base+1 e hi-1 não dá
        n_hi = cadeiras_bloco(uf, leg[uf], cands[uf], mb, hi)[0]
        n_lo = cadeiras_bloco(uf, leg[uf], cands[uf], mb, hi - 1)[0]
        assert n_hi == base + 1 and n_lo == base, (uf, n_hi, n_lo, base)
        validos = sum(e['votos'] for e in ent.values())
        linhas.append([uf, CADEIRAS[uf], base, votos, round(100 * votos / validos, 2), qe, hi,
                       round(100 * hi / votos, 2), round(hi / qe, 3)])
    linhas.sort(key=lambda r: r[6])
    with open(f'{saida}/votos_para_mais_uma_cadeira.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['uf', 'cadeiras_uf', 'cadeiras_bloco_B', 'votos_bloco', 'pct_validos',
                    'qe', 'votos_adicionais', 'pct_sobre_votos_bloco', 'em_quocientes_eleitorais'])
        w.writerows(linhas)
    return linhas


if __name__ == '__main__':
    main(*sys.argv[1:4])
