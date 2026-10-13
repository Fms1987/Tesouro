"""Votos (legenda + candidatos) que faltaram ao bloco B para ganhar mais 1 cadeira por UF.
Votos dos demais e quociente eleitoral mantidos fixos (acréscimo puro ao bloco).

Uso: python3 faltantes.py <dir_partido_munzona> <dir_candidato_munzona> <dir_saida> [B|C]
"""
import csv
import sys

from simulacao import BLOCO_B, BLOCO_C, CADEIRAS, NOME_B, NOME_C, carregar, distribuir


def main(dir_part, dir_cand, saida, cenario='B'):
    BLOCO, NOME = {'B': (BLOCO_B, NOME_B), 'C': (BLOCO_C, NOME_C)}[cenario]
    leg, cands, ent_a = carregar(dir_part, dir_cand)
    linhas = []
    for uf in CADEIRAS:
        mb = {p: (NOME if p in BLOCO else e) for p, e in ent_a[uf].items()}
        qe, validos, ent0, _ = distribuir(uf, CADEIRAS[uf], leg[uf], cands[uf], mb)

        base = ent0[NOME]['n']
        lista = ent0[NOME]['cands']                 # ordenada por votos
        sq_prox = lista[base][1]                      # próximo candidato do bloco, não eleito
        v_prox = lista[base][0]

        def rodar(extra):
            c2 = {k: dict(v) for k, v in cands[uf].items()}
            c2[sq_prox]['v'] += extra
            return distribuir(uf, CADEIRAS[uf], leg[uf], c2, mb, qe_fixo=qe)


        hi = 1
        while rodar(hi)[2][NOME]['n'] <= base:
            hi *= 2
            assert hi < 10**8, uf
        lo = hi // 2
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if rodar(mid)[2][NOME]['n'] > base: hi = mid
            else: lo = mid
        # verificação por varredura: nenhum valor menor dá cadeira extra (amostra densa)
        for x in list(range(max(0, hi - 150), hi)) + list(range(0, hi, max(1, hi // 60))):
            assert rodar(x)[2][NOME]['n'] == base, (uf, x)
        ent1 = rodar(hi)[2]
        perde = [n for n in ent0 if n != NOME and ent1[n]['n'] < ent0[n]['n']]
        votos = ent0[NOME]['votos']
        leg_b = ent0[NOME]['leg']
        linhas.append([uf, CADEIRAS[uf], base, base + 1, votos, leg_b, ent0[NOME]['nom'], qe, hi,
                       round(100 * hi / votos, 2), round(hi / qe, 3), cands[uf][sq_prox]['nome'], cands[uf][sq_prox]['partido'], v_prox, '; '.join(perde)])
    linhas.sort(key=lambda r: r[8])
    with open(f'{saida}/votos_faltantes_mais_uma_cadeira.csv' if cenario == 'B' else f'{saida}/votos_faltantes_cenario_C.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['uf', 'cadeiras_uf', 'cadeiras_bloco_B', 'cadeiras_com_acrescimo', 'votos_bloco',
                    'votos_legenda', 'votos_nominais', 'qe', 'votos_faltantes',
                    'pct_sobre_votos_bloco', 'em_quocientes_eleitorais', 'proximo_candidato', 'partido', 'votos_do_candidato', 'cadeira_tirada_de'])
        w.writerows(linhas)
    return linhas


if __name__ == '__main__':
    main(*sys.argv[1:5])
