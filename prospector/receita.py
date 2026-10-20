"""Dados abertos de CNPJ da Receita Federal: download e leitura em fluxo.

Onde estão (conferido em 20/10/2026): compartilhamento público do Nextcloud da Receita,
https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9 , uma pasta por mês (AAAA-MM).
O acesso por WebDAV usa o token do compartilhamento como usuário, sem senha.

Layout (sem cabeçalho, ';' como separador, campos entre aspas, latin-1):
  Estabelecimentos: 30 colunas (ver COL_EST)
  Empresas: cnpj_basico; razao_social; natureza_juridica; qualificacao_responsavel; capital_social; porte; ente_federativo
  Simples: cnpj_basico; opcao_simples; data_opcao; data_exclusao; opcao_mei; data_opcao_mei; data_exclusao_mei
  Cnaes / Municipios: codigo; descricao
"""
import csv
import io
import os
import re
import time
import urllib.request
import zipfile
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor

TOKEN = 'YggdBLfdninEJX9'
WEBDAV = 'https://arquivos.receitafederal.gov.br/public.php/webdav/'

COL_EST = ['cnpj_basico', 'cnpj_ordem', 'cnpj_dv', 'matriz_filial', 'nome_fantasia', 'situacao', 'data_situacao',
           'motivo_situacao', 'cidade_exterior', 'pais', 'data_inicio', 'cnae_principal', 'cnaes_secundarios',
           'tipo_logradouro', 'logradouro', 'numero', 'complemento', 'bairro', 'cep', 'uf', 'municipio',
           'ddd1', 'telefone1', 'ddd2', 'telefone2', 'ddd_fax', 'fax', 'email', 'situacao_especial',
           'data_situacao_especial']
ATIVA = '02'


def _req(caminho, metodo='GET', extra=None):
    cab = {'Authorization': 'Basic ' + b64encode((TOKEN + ':').encode()).decode()}
    cab.update(extra or {})
    return urllib.request.Request(WEBDAV + caminho, method=metodo, headers=cab)


def listar_meses():
    """Pastas AAAA-MM publicadas, da mais antiga para a mais nova."""
    with urllib.request.urlopen(_req('', 'PROPFIND', {'Depth': '1'}), timeout=60) as r:
        xml = r.read().decode('utf-8', 'replace')
    return sorted(set(re.findall(r'/public\.php/webdav/(\d{4}-\d{2})/', xml)))


def baixar(mes, nome, pasta, tentativas=6, avisar=print):
    """Baixa <mes>/<nome> para <pasta>, retomando de onde parou (Range) se a conexão cair."""
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, mes + '-' + nome)
    parcial = destino + '.parcial'
    if os.path.exists(destino):
        return destino
    for n in range(1, tentativas + 1):
        ja = os.path.getsize(parcial) if os.path.exists(parcial) else 0
        try:
            req = _req(mes + '/' + nome, extra={'Range': 'bytes=%d-' % ja} if ja else None)
            with urllib.request.urlopen(req, timeout=120) as r:
                if ja and r.status != 206:  # servidor ignorou o Range: recomeça
                    ja = 0
                with open(parcial, 'ab' if ja else 'wb') as f:
                    while True:
                        bloco = r.read(1 << 20)
                        if not bloco:
                            break
                        f.write(bloco)
            os.replace(parcial, destino)
            return destino
        except OSError as e:  # urllib.error.URLError é OSError
            avisar('  %s: conexão caiu (%s), tentativa %d/%d' % (nome, e, n, tentativas))
            time.sleep(min(2 ** n, 30))
    raise RuntimeError('não consegui baixar %s/%s' % (mes, nome))


def baixar_em_ordem(mes, nomes, pasta, paralelo=3, avisar=print):
    """Baixa vários arquivos com `paralelo` conexões e entrega os caminhos na ordem pedida, assim que cada um fica
    pronto. O servidor da Receita é lento por conexão (~1 MB/s); em paralelo o total cai bastante."""
    with ThreadPoolExecutor(max_workers=paralelo) as ex:
        futuros = [ex.submit(baixar, mes, n, pasta, avisar=avisar) for n in nomes]
        for f in futuros:
            yield f.result()


def linhas(caminho_zip):
    """Lê o CSV de dentro do zip, linha a linha, sem extrair para o disco."""
    with zipfile.ZipFile(caminho_zip) as z:
        for nome in z.namelist():
            with z.open(nome) as bruto:
                texto = io.TextIOWrapper(bruto, encoding='latin-1', newline='')
                for linha in texto:
                    yield linha


def campos(linha):
    """Separa uma linha ("a";"b";...). Rápido para o caso comum; cai no csv se houver aspas no meio."""
    s = linha.rstrip('\r\n')
    if s.startswith('"') and s.endswith('"'):
        partes = s[1:-1].split('";"')
        if '"' not in ''.join(partes):
            return partes
    return next(csv.reader([s], delimiter=';'))


def tabela(caminho_zip):
    """Tabela de referência (Cnaes, Municipios...): {codigo: descricao}."""
    return {c[0]: c[1] for c in map(campos, linhas(caminho_zip)) if len(c) >= 2}
