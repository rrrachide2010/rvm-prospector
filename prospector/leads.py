"""Filtro, limpeza, pontuação e exportação dos leads.

Regras de dado pessoal (ver docs/LGPD.md):
  - não lê o arquivo de Sócios;
  - tira o CPF que a Receita cola no fim da razão social de MEI e empresário individual;
  - respeita a lista de "não contatar" (CNPJ ou telefone);
  - toda linha leva a fonte e o mês da base.
"""
import csv
import re
from datetime import date

from .nichos import NICHOS

PORTE = {'00': 'não informado', '01': 'microempresa', '03': 'pequeno porte', '05': 'demais'}
NAT_PESSOA = {'2135'}  # Empresário (Individual): a razão social é o nome da pessoa

COLUNAS = ['pontos', 'por_que', 'nicho', 'sistema_sugerido', 'dor', 'nome', 'cnpj', 'matriz_filial', 'abertura',
           'anos', 'porte', 'mei', 'cnae', 'bairro', 'endereco', 'cep', 'cidade', 'uf', 'telefone', 'whatsapp',
           'telefone2', 'email', 'aviso_email', 'fonte']


def tirar_cpf(razao):
    """'MARIA DA SILVA 12345678901' -> 'MARIA DA SILVA'. Só corta 11 dígitos no fim."""
    return re.sub(r'\s*\d{11}\s*$', '', razao or '').strip()


def telefone(ddd, numero):
    """(texto formatado, é celular?).

    A Receita guarda quase todo telefone com 8 dígitos, inclusive celular cadastrado antes do nono dígito
    (base 2026-10 de Sorocaba: 98% com 8 dígitos). Fixo começa com 2 a 5; com 8 dígitos começando com 6 a 9 é
    celular antigo, e ganha o 9 na frente. Com 9 dígitos, celular começa com 9."""
    ddd = re.sub(r'\D', '', ddd or '')
    num = re.sub(r'\D', '', numero or '')
    if not ddd or len(num) < 8:
        return '', False
    ddd = ddd[-2:]
    if len(num) == 8 and num[0] in '6789':
        num = '9' + num
    cel = len(num) == 9 and num.startswith('9')
    fmt = '(%s) %s-%s' % (ddd, num[:-4], num[-4:])
    return fmt, cel


def nome_fantasia(bruto):
    """Limpa o nome fantasia: sem CPF no fim, sem aspas em volta, e vazio quando não tem letra ('***', '000')."""
    nome = tirar_cpf(bruto).strip().strip('\'"*').strip()
    return nome if re.search(r'[A-Za-zÀ-ÿ]', nome) else ''


def anos_desde(aaaammdd, hoje=None):
    hoje = hoje or date.today()
    try:
        d = date(int(aaaammdd[:4]), int(aaaammdd[4:6]), int(aaaammdd[6:8]))
    except (ValueError, TypeError):
        return None
    return (hoje - d).days / 365.25


def filtrar_estabelecimento(c, municipio, uf, mapa_cnae, secundaria=False):
    """Chave do nicho se o estabelecimento (lista de 30 campos) entra; None se não entra."""
    if len(c) < 30 or c[5] != '02' or c[20] != municipio or c[19] != uf:
        return None
    nicho = mapa_cnae.get(c[11])
    if nicho is None and secundaria and c[12]:
        nicho = next((mapa_cnae[x] for x in c[12].split(',') if x in mapa_cnae), None)
    return nicho


def pontuar(lead):
    """Pontos de 0 a 100, com o motivo de cada um (a planilha mostra o porquê)."""
    pts, motivo = 0, []

    def soma(n, txt):
        nonlocal pts
        pts += n
        motivo.append('%+d %s' % (n, txt))

    anos = lead['anos']
    if anos is not None and anos >= 5:
        soma(30, '5+ anos aberto')
    elif anos is not None and anos >= 2:
        soma(20, '2+ anos aberto')
    elif anos is not None and anos >= 1:
        soma(5, '1+ ano aberto')
    if lead['whatsapp']:
        soma(25, 'celular (dá para chamar no WhatsApp)')
    elif lead['telefone']:
        soma(10, 'telefone fixo')
    if lead['email'] and not lead['aviso_email']:
        soma(10, 'e-mail')
    if lead['mei'] == 'sim':
        soma(5, 'MEI (ticket menor)')
    elif lead['porte'] in ('microempresa', 'pequeno porte'):
        soma(25, lead['porte'])
    elif lead['porte'] == 'demais':
        soma(15, 'porte maior (decisão pode ser central)')
    if lead['matriz_filial'] == 'filial':
        soma(-10, 'filial')
    if lead['tem_fantasia']:
        soma(10, 'nome fantasia (marca para o público)')
    return max(0, min(100, pts)), '; '.join(motivo)


def montar(c, nicho, empresa, simples, cidade, fonte, hoje=None):
    """Lead (dict) a partir dos campos do estabelecimento + dados da empresa e do Simples."""
    razao, natureza, porte = empresa or ('', '', '')
    razao = tirar_cpf(razao)
    fantasia = nome_fantasia(c[4])
    tel1, cel1 = telefone(c[21], c[22])
    tel2, cel2 = telefone(c[23], c[24])
    cel = tel1 if cel1 else (tel2 if cel2 else '')
    email = c[27].strip().lower()
    aviso = 'provável e-mail do contador' if re.search(r'contab|contador|escrit', email) else ''
    anos = anos_desde(c[10], hoje)
    lead = {
        'nicho': NICHOS[nicho]['nome'],
        'sistema_sugerido': NICHOS[nicho]['sistema'],
        'dor': NICHOS[nicho]['dor'],
        'nome': fantasia or razao,
        'tem_fantasia': bool(fantasia),
        'cnpj': '%s.%s.%s/%s-%s' % (c[0][:2], c[0][2:5], c[0][5:8], c[1], c[2]),
        'matriz_filial': 'matriz' if c[3] == '1' else 'filial',
        'abertura': '%s/%s/%s' % (c[10][6:8], c[10][4:6], c[10][:4]) if len(c[10]) == 8 else '',
        'anos': round(anos, 1) if anos is not None else None,
        'porte': PORTE.get(porte, ''),
        'mei': 'sim' if simples == 'S' else ('não' if simples == 'N' else ''),
        'cnae': c[11],
        'bairro': c[17].strip(),
        'endereco': ' '.join(x for x in (c[13], c[14] + ',' if c[14] else '', c[15], c[16]) if x).strip(),
        'cep': c[18],
        'cidade': cidade,
        'uf': c[19],
        'telefone': tel1,
        'whatsapp': 'https://wa.me/55' + re.sub(r'\D', '', cel) if cel else '',
        'telefone2': tel2,
        'email': email,
        'aviso_email': aviso,
        'fonte': fonte,
        'natureza': natureza,
    }
    lead['pontos'], lead['por_que'] = pontuar(lead)
    return lead


def carregar_nao_contatar(caminho):
    """CNPJs (só dígitos) e telefones (só dígitos) de quem pediu para não ser contatado."""
    if not caminho:
        return set()
    with open(caminho, encoding='utf-8') as f:
        return {re.sub(r'\D', '', x) for x in f.read().split() if re.sub(r'\D', '', x)}


def bloqueado(lead, nao_contatar):
    chaves = {re.sub(r'\D', '', lead['cnpj']), re.sub(r'\D', '', lead['telefone']),
              re.sub(r'\D', '', lead['telefone2'])}
    return bool(nao_contatar & {k for k in chaves if k})


def exportar(leads, caminho):
    """CSV em UTF-8 com BOM (abre certo no Excel): mais pontos primeiro; no empate, o mais antigo."""
    leads = sorted(leads, key=lambda l: (-l['pontos'], -(l['anos'] or 0), l['nome']))
    with open(caminho, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, extrasaction='ignore', delimiter=';')
        w.writeheader()
        for l in leads:
            w.writerow(l)
    return len(leads)
