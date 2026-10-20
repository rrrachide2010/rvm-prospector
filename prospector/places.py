"""Enriquecimento opcional pela Google Places API (New), Text Search.

Só roda com a chave em GOOGLE_PLACES_API_KEY (variável de ambiente, nunca no código) e com --confirmar.
Sem --confirmar, mostra quantas chamadas faria e o SKU, e para.

SKU por campo (doc oficial de Text Search, conferida em 20/10/2026):
  basico   -> places.id, displayName, formattedAddress, googleMapsUri, businessStatus: Text Search Pro
  completo -> + websiteUri, rating, userRatingCount: Text Search Enterprise (a chamada inteira cobra o SKU mais alto)
Preço e cota gratuita mudam: confira https://developers.google.com/maps/billing-and-pricing antes de rodar.

Guarda: place_id e link do Maps. Os demais campos são consulta pontual com data (ver docs/LGPD.md, item Google).
"""
import csv
import difflib
import json
import os
import unicodedata
import urllib.request
from datetime import date

URL = 'https://places.googleapis.com/v1/places:searchText'
CAMPOS = {
    'basico': ['places.id', 'places.displayName', 'places.formattedAddress', 'places.googleMapsUri',
               'places.businessStatus'],
}
CAMPOS['completo'] = CAMPOS['basico'] + ['places.websiteUri', 'places.rating', 'places.userRatingCount']
SKU = {'basico': 'Text Search Pro', 'completo': 'Text Search Enterprise'}
NOVAS = ['google_place_id', 'google_maps', 'google_status', 'google_site', 'google_nota', 'google_avaliacoes',
         'google_confianca', 'google_consultado_em']


def _norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return ' '.join(w for w in s.replace('-', ' ').split() if w not in ('ltda', 'me', 'epp', 'eireli', 'sa'))


def parecido(a, b):
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def consultar(lead, chave, campos='basico', abrir=urllib.request.urlopen):
    corpo = {'textQuery': '%s %s %s %s' % (lead['nome'], lead['bairro'], lead['cidade'], lead['uf']),
             'languageCode': 'pt-BR', 'regionCode': 'BR', 'pageSize': 1}
    req = urllib.request.Request(URL, data=json.dumps(corpo).encode(), method='POST', headers={
        'Content-Type': 'application/json', 'X-Goog-Api-Key': chave,
        'X-Goog-FieldMask': ','.join(CAMPOS[campos])})
    with abrir(req, timeout=30) as r:
        dados = json.loads(r.read().decode())
    lugares = dados.get('places') or []
    if not lugares:
        return {'google_confianca': 'não encontrado'}
    p = lugares[0]
    nome = (p.get('displayName') or {}).get('text', '')
    nota = parecido(nome, lead['nome'])
    return {
        'google_place_id': p.get('id', ''),
        'google_maps': p.get('googleMapsUri', ''),
        'google_status': p.get('businessStatus', ''),
        'google_site': p.get('websiteUri', ''),
        'google_nota': p.get('rating', ''),
        'google_avaliacoes': p.get('userRatingCount', ''),
        'google_confianca': 'alta' if nota >= 0.75 else ('média' if nota >= 0.5 else 'baixa: confira (%s)' % nome),
    }


def enriquecer(entrada, saida, limite, campos='basico', confirmar=False, chave=None, abrir=urllib.request.urlopen,
               avisar=print):
    with open(entrada, encoding='utf-8-sig', newline='') as f:
        leitor = csv.DictReader(f, delimiter=';')
        colunas = leitor.fieldnames
        linhas = list(leitor)
    alvo = linhas[:limite]
    avisar('%d chamadas de %s (%d linhas no arquivo; só as %d primeiras, que são as de mais pontos).'
           % (len(alvo), SKU[campos], len(linhas), len(alvo)))
    if not confirmar:
        avisar('Nada foi consultado. Confira o preço do SKU e rode de novo com --confirmar.')
        return 0
    chave = chave or os.environ.get('GOOGLE_PLACES_API_KEY')
    if not chave:
        raise SystemExit('Falta GOOGLE_PLACES_API_KEY no ambiente.')
    hoje = date.today().isoformat()
    for i, lead in enumerate(alvo, 1):
        try:
            lead.update(consultar(lead, chave, campos, abrir))
        except OSError as e:
            lead['google_confianca'] = 'erro: %s' % e
        lead['google_consultado_em'] = hoje
        if i % 10 == 0:
            avisar('  %d/%d' % (i, len(alvo)))
    with open(saida, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=colunas + [c for c in NOVAS if c not in colunas], delimiter=';')
        w.writeheader()
        w.writerows(linhas)
    return len(alvo)
