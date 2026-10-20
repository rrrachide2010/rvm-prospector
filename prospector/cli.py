"""Linha de comando do RVM Prospector.

  python -m prospector nichos [--conferir]
  python -m prospector cidade  --uf SP --municipio SOROCABA[,VOTORANTIM] [--mes 2026-10]
  python -m prospector leads   --uf SP --municipio SOROCABA [--nichos beleza,saude] [--anos-min 2] [--saida x.csv]
  python -m prospector enriquecer --entrada x.csv --saida y.csv --limite 50 [--campos basico|completo] [--confirmar]

"cidade" varre a base nacional uma vez e guarda só os estabelecimentos ativos da(s) cidade(s), com
empresa e Simples, em dados/. "leads" filtra esse recorte por nicho, pontua e exporta, sem rede.
"""
import argparse
import csv
import json
import os
import sys
import unicodedata

from . import leads as L
from . import receita as R
from .nichos import NICHOS, cnae_para_nicho

DADOS = os.environ.get('PROSPECTOR_DADOS', 'dados')


def _sem_acento(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().upper().strip()


def _mes(args):
    return args.mes or R.listar_meses()[-1]


def _ref(mes, nome):
    return R.tabela(R.baixar(mes, nome + '.zip', DADOS))


def _codigos_municipio(mes, nomes):
    tab = _ref(mes, 'Municipios')
    por_nome = {}
    for cod, nome in tab.items():
        por_nome.setdefault(_sem_acento(nome), []).append(cod)
    saida = {}
    for n in nomes:
        cods = por_nome.get(_sem_acento(n))
        if not cods:
            raise SystemExit('Município não encontrado na tabela da Receita: %s' % n)
        for c in cods:
            saida[c] = tab[c]
    return saida


def _recorte(mes, uf, cods):
    base = os.path.join(DADOS, 'recorte-%s-%s-%s' % (mes, uf, '-'.join(sorted(cods))))
    return base + '-estab.csv', base + '-empresas.json', base + '-simples.json'


def cmd_cidade(args):
    mes = _mes(args)
    uf = args.uf.upper()
    cods = _codigos_municipio(mes, args.municipio.split(','))
    print('Base %s · %s · %s' % (mes, uf, ', '.join('%s (%s)' % (v, k) for k, v in cods.items())))
    arq_est, arq_emp, arq_sim = _recorte(mes, uf, cods)
    chaves = ['"%s";"%s"' % (uf, c) for c in cods]  # uf e município são colunas vizinhas: filtro rápido
    basicos, total = set(), 0
    with open(arq_est + '.parcial', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';')
        for i in range(10):
            z = R.baixar(mes, 'Estabelecimentos%d.zip' % i, DADOS)
            n = 0
            for linha in R.linhas(z):
                if any(k in linha for k in chaves):
                    c = R.campos(linha)
                    if len(c) >= 30 and c[5] == R.ATIVA and c[19] == uf and c[20] in cods:
                        w.writerow(c)
                        basicos.add(c[0])
                        n += 1
            total += n
            print('  Estabelecimentos%d: %d ativos na cidade' % (i, n))
            if not args.manter_zips:
                os.remove(z)
    os.replace(arq_est + '.parcial', arq_est)

    empresas = {}
    for i in range(10):
        z = R.baixar(mes, 'Empresas%d.zip' % i, DADOS)
        for linha in R.linhas(z):
            if linha[1:9] in basicos:
                c = R.campos(linha)
                empresas[c[0]] = (c[1], c[2], c[5] if len(c) > 5 else '')
        print('  Empresas%d: %d empresas da cidade até agora' % (i, len(empresas)))
        if not args.manter_zips:
            os.remove(z)
    with open(arq_emp, 'w', encoding='utf-8') as f:
        json.dump(empresas, f, ensure_ascii=False)

    simples = {}
    z = R.baixar(mes, 'Simples.zip', DADOS)
    for linha in R.linhas(z):
        if linha[1:9] in basicos:
            c = R.campos(linha)
            simples[c[0]] = c[4] if len(c) > 4 else ''
    if not args.manter_zips:
        os.remove(z)
    with open(arq_sim, 'w', encoding='utf-8') as f:
        json.dump(simples, f)
    print('Pronto: %d estabelecimentos ativos, %d empresas, %d no Simples. Recorte em %s'
          % (total, len(empresas), len(simples), DADOS))


def cmd_leads(args):
    mes = _mes(args)
    uf = args.uf.upper()
    cods = _codigos_municipio(mes, args.municipio.split(','))
    arq_est, arq_emp, arq_sim = _recorte(mes, uf, cods)
    if not os.path.exists(arq_est):
        raise SystemExit('Recorte não encontrado. Rode antes: python -m prospector cidade --uf %s --municipio %s'
                         % (uf, args.municipio))
    with open(arq_emp, encoding='utf-8') as f:
        empresas = json.load(f)
    with open(arq_sim, encoding='utf-8') as f:
        simples = json.load(f)
    mapa = cnae_para_nicho(args.nichos.split(',') if args.nichos else None)
    bloquear = L.carregar_nao_contatar(args.nao_contatar)
    fonte = 'Receita Federal, dados abertos CNPJ %s' % mes
    saida, fora = [], 0
    with open(arq_est, encoding='utf-8', newline='') as f:
        for c in csv.reader(f, delimiter=';'):
            nicho = L.filtrar_estabelecimento(c, c[20], uf, mapa, args.secundaria)
            if not nicho:
                continue
            lead = L.montar(c, nicho, empresas.get(c[0]), simples.get(c[0]), cods[c[20]], fonte)
            if (lead['anos'] or 0) < args.anos_min:
                continue
            if L.bloqueado(lead, bloquear):
                fora += 1
                continue
            saida.append(lead)
    caminho = args.saida or 'leads-%s-%s.csv' % (_sem_acento(args.municipio.split(',')[0]).lower(), mes)
    n = L.exportar(saida, caminho)
    print('%d leads em %s (%d fora pela lista de não contatar).' % (n, caminho, fora))
    por = {}
    for l in saida:
        por[l['nicho']] = por.get(l['nicho'], 0) + 1
    for nome, q in sorted(por.items(), key=lambda x: -x[1]):
        print('  %-36s %d' % (nome, q))


def cmd_nichos(args):
    cnaes = _ref(_mes(args), 'Cnaes') if args.conferir else {}
    erro = False
    for chave, n in NICHOS.items():
        print('%-12s %s -> %s' % (chave, n['nome'], n['sistema']))
        for c in n['cnaes']:
            desc = cnaes.get(c, '') if args.conferir else ''
            if args.conferir and not desc:
                erro = True
                desc = 'NÃO EXISTE NA TABELA DA RECEITA'
            print('             %s %s' % (c, desc))
    if erro:
        raise SystemExit(1)


def cmd_enriquecer(args):
    from .places import enriquecer
    enriquecer(args.entrada, args.saida, args.limite, args.campos, args.confirmar)


def main(argv=None):
    p = argparse.ArgumentParser(prog='prospector', description='Lista de prospecção a partir do CNPJ aberto.')
    sub = p.add_subparsers(dest='cmd', required=True)

    a = sub.add_parser('nichos', help='lista os nichos e CNAEs')
    a.add_argument('--conferir', action='store_true', help='confere os CNAEs na tabela da Receita')
    a.add_argument('--mes')
    a.set_defaults(f=cmd_nichos)

    a = sub.add_parser('cidade', help='baixa a base e guarda o recorte da cidade')
    a.add_argument('--uf', required=True)
    a.add_argument('--municipio', required=True, help='nome como na Receita; vários separados por vírgula')
    a.add_argument('--mes', help='AAAA-MM (padrão: o mais recente)')
    a.add_argument('--manter-zips', action='store_true', help='não apaga os zips depois de ler')
    a.set_defaults(f=cmd_cidade)

    a = sub.add_parser('leads', help='filtra o recorte por nicho, pontua e exporta CSV')
    a.add_argument('--uf', required=True)
    a.add_argument('--municipio', required=True)
    a.add_argument('--mes')
    a.add_argument('--nichos', help='chaves separadas por vírgula (padrão: todos). Ver: prospector nichos')
    a.add_argument('--anos-min', type=float, default=1)
    a.add_argument('--secundaria', action='store_true', help='aceita CNAE secundário do nicho')
    a.add_argument('--nao-contatar', help='arquivo com CNPJs/telefones que pediram para não ser contatados')
    a.add_argument('--saida')
    a.set_defaults(f=cmd_leads)

    a = sub.add_parser('enriquecer', help='Google Places (opcional, pago por uso)')
    a.add_argument('--entrada', required=True)
    a.add_argument('--saida', required=True)
    a.add_argument('--limite', type=int, default=50)
    a.add_argument('--campos', choices=['basico', 'completo'], default='basico')
    a.add_argument('--confirmar', action='store_true')
    a.set_defaults(f=cmd_enriquecer)

    args = p.parse_args(argv)
    args.f(args)


if __name__ == '__main__':
    sys.exit(main())
