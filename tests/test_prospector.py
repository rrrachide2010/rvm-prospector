"""Testes do RVM Prospector com dados sintéticos (CNPJs e pessoas fictícios). Sem rede.

Rodar: python -m unittest discover -s tests -v
"""
import csv
import io
import json
import os
import tempfile
import unittest
import zipfile
from datetime import date
from unittest import mock

from prospector import leads as L
from prospector import places as P
from prospector import receita as R
from prospector import cli
from prospector.nichos import NICHOS, cnae_para_nicho

HOJE = date(2026, 10, 20)


def estab(basico='11222333', ordem='0001', dv='81', mf='1', fantasia='BARBEARIA DO TESTE', situacao='02',
          inicio='20180315', cnae='9602501', sec='', bairro='CENTRO', uf='SP', mun='7145', ddd1='15',
          tel1='991234567', ddd2='', tel2='', email='contato@barbeariateste.com.br'):
    c = [''] * 30
    c[0], c[1], c[2], c[3], c[4], c[5] = basico, ordem, dv, mf, fantasia, situacao
    c[10], c[11], c[12] = inicio, cnae, sec
    c[13], c[14], c[15], c[17], c[18], c[19], c[20] = 'RUA', 'DAS FLORES', '100', bairro, '18000000', uf, mun
    c[21], c[22], c[23], c[24], c[27] = ddd1, tel1, ddd2, tel2, email
    return c


def linha_csv(c):
    return '"' + '";"'.join(c) + '"\r\n'


def zip_com(caminho, linhas):
    with zipfile.ZipFile(caminho, 'w') as z:
        z.writestr('DADOS.CSV', ''.join(linhas).encode('latin-1'))


class TesteLimpeza(unittest.TestCase):
    def test_tira_cpf_do_fim_da_razao_social(self):
        self.assertEqual(L.tirar_cpf('MARIA FICTICIA DA SILVA 12345678901'), 'MARIA FICTICIA DA SILVA')
        self.assertEqual(L.tirar_cpf('OFICINA 2000 LTDA'), 'OFICINA 2000 LTDA')

    def test_telefone_celular_e_fixo(self):
        self.assertEqual(L.telefone('15', '991234567'), ('(15) 99123-4567', True))
        self.assertEqual(L.telefone('015', '32345678'), ('(15) 3234-5678', False))
        self.assertEqual(L.telefone('', '32345678'), ('', False))

    def test_celular_de_8_digitos_da_receita_ganha_o_nono(self):
        self.assertEqual(L.telefone('15', '96916290'), ('(15) 99691-6290', True))
        self.assertEqual(L.telefone('15', '81140471'), ('(15) 98114-0471', True))
        self.assertEqual(L.telefone('15', '22345678'), ('(15) 2234-5678', False))

    def test_nome_fantasia_lixo_vira_vazio(self):
        self.assertEqual(L.nome_fantasia('****'), '')
        self.assertEqual(L.nome_fantasia('000000000000000000'), '')
        self.assertEqual(L.nome_fantasia("''A. R. NEURO''"), 'A. R. NEURO')
        self.assertEqual(L.nome_fantasia('*S&M CONSTRUTORA*'), 'S&M CONSTRUTORA')
        self.assertEqual(L.nome_fantasia('JOANA FICTICIA 12345678901'), 'JOANA FICTICIA')

    def test_campos_rapido_e_com_aspas(self):
        self.assertEqual(R.campos('"a";"b";"c"\r\n'), ['a', 'b', 'c'])
        self.assertEqual(R.campos('"a";"tem ""aspas""";"c"\n'), ['a', 'tem "aspas"', 'c'])


class TesteFiltroEPontos(unittest.TestCase):
    mapa = cnae_para_nicho(['beleza'])

    def test_filtra_cidade_uf_situacao_e_cnae(self):
        self.assertEqual(L.filtrar_estabelecimento(estab(), '7145', 'SP', self.mapa), 'beleza')
        self.assertIsNone(L.filtrar_estabelecimento(estab(situacao='08'), '7145', 'SP', self.mapa))
        self.assertIsNone(L.filtrar_estabelecimento(estab(uf='MG'), '7145', 'SP', self.mapa))
        self.assertIsNone(L.filtrar_estabelecimento(estab(cnae='4520001'), '7145', 'SP', self.mapa))

    def test_cnae_secundario_so_com_a_opcao(self):
        c = estab(cnae='4781400', sec='4782201,9602501')
        self.assertIsNone(L.filtrar_estabelecimento(c, '7145', 'SP', self.mapa))
        self.assertEqual(L.filtrar_estabelecimento(c, '7145', 'SP', self.mapa, secundaria=True), 'beleza')

    def test_lead_completo_e_pontos_explicados(self):
        lead = L.montar(estab(), 'beleza', ('JOAO FICTICIO 12345678901', '2135', '01'), 'N', 'SOROCABA', 'fonte', HOJE)
        self.assertEqual(lead['nome'], 'BARBEARIA DO TESTE')
        self.assertEqual(lead['cnpj'], '11.222.333/0001-81')
        self.assertEqual(lead['whatsapp'], 'https://wa.me/5515991234567')
        self.assertEqual(lead['sistema_sugerido'], NICHOS['beleza']['sistema'])
        # 8 anos (+30), celular (+25), e-mail (+10), microempresa (+25), nome fantasia (+10)
        self.assertEqual(lead['pontos'], 100)
        self.assertIn('celular', lead['por_que'])

    def test_sem_fantasia_usa_razao_sem_cpf_e_mei_pontua_menos(self):
        lead = L.montar(estab(fantasia='', email=''), 'beleza', ('ANA FICTICIA 98765432100', '2135', '01'), 'S',
                        'SOROCABA', 'fonte', HOJE)
        self.assertEqual(lead['nome'], 'ANA FICTICIA')
        self.assertNotIn('98765432100', json.dumps(lead))
        self.assertEqual(lead['mei'], 'sim')
        self.assertIn('MEI', lead['por_que'])

    def test_email_de_contador_nao_pontua(self):
        lead = L.montar(estab(email='fiscal@contabilidadexyz.com.br'), 'beleza', None, '', 'SOROCABA', 'f', HOJE)
        self.assertEqual(lead['aviso_email'], 'provável e-mail do contador')
        self.assertNotIn('+10 e-mail', lead['por_que'])

    def test_nao_contatar_por_cnpj_ou_telefone(self):
        lead = L.montar(estab(), 'beleza', None, '', 'SOROCABA', 'f', HOJE)
        self.assertTrue(L.bloqueado(lead, {'11222333000181'}))
        self.assertTrue(L.bloqueado(lead, {'15991234567'}))
        self.assertFalse(L.bloqueado(lead, {'99999999000199'}))


class TesteNichos(unittest.TestCase):
    def test_cnae_em_um_nicho_so(self):
        vistos = {}
        for chave, n in NICHOS.items():
            for c in n['cnaes']:
                self.assertNotIn(c, vistos, '%s em %s e %s' % (c, vistos.get(c), chave))
                self.assertRegex(c, r'^\d{7}$')
                vistos[c] = chave

    def test_nicho_desconhecido(self):
        with self.assertRaises(ValueError):
            cnae_para_nicho(['astronautas'])

    def test_setor_saude_cobre_o_universo_pedido(self):
        mapa = cnae_para_nicho(['saude'])
        esperado = {
            '8630503': 'medico',             # consultório médico
            '8630504': 'odonto',
            '8640202': 'laboratorio',        # laboratório clínico
            '4771701': 'farmacia',
            '4771702': 'farmacia',           # manipulação
            '4773300': 'artigos_medicos',    # loja cirúrgica e ortopédica
            '8650004': 'fisioterapia',
            '8650002': 'nutricao',
            '8650003': 'psicologia',
            '8650006': 'fonoaudiologia',
            '8610101': 'hospital',
            '8712300': 'enfermagem',         # home care
            '4645101': 'distribuidora_saude',
            '4774100': 'otica',
        }
        for cnae, nicho in esperado.items():
            self.assertEqual(mapa.get(cnae), nicho, cnae)
        self.assertNotIn('4771704', mapa, 'farmácia veterinária fica fora')
        self.assertNotIn('6550200', mapa, 'plano de saúde fica fora')
        self.assertNotIn('9602501', mapa, 'beleza não é saúde')

    def test_setor_mistura_com_nicho_sem_repetir(self):
        from prospector.nichos import SETORES, expandir
        self.assertEqual(expandir(['beleza', 'saude', 'farmacia'])[:2], ['beleza', SETORES['saude'][0]])
        self.assertEqual(len(expandir(['saude', 'farmacia'])), len(SETORES['saude']))
        mapa = cnae_para_nicho(['beleza', 'saude'])
        self.assertEqual(mapa['9602501'], 'beleza')
        self.assertEqual(mapa['4773300'], 'artigos_medicos')


class TesteFluxoCompleto(unittest.TestCase):
    """cidade + leads de ponta a ponta, com a 'base nacional' falsa em zips locais."""

    def test_cidade_e_leads(self):
        with tempfile.TemporaryDirectory() as d:
            mes = '2026-10'
            zip_com(os.path.join(d, mes + '-Municipios.zip'), [linha_csv(['7145', 'SOROCABA']),
                                                                linha_csv(['9999', 'OUTRA'])])
            dentro = estab()
            velha_fechada = estab(basico='44555666', situacao='08')
            outra_cidade = estab(basico='77888999', mun='9999')
            oficina = estab(basico='12121212', fantasia='OFICINA FICTICIA', cnae='4520001', tel1='32345678')
            nova = estab(basico='13131313', fantasia='SALAO NOVO', inicio='20260901')
            zip_com(os.path.join(d, mes + '-Estabelecimentos0.zip'),
                    [linha_csv(x) for x in (dentro, velha_fechada, outra_cidade, oficina, nova)])
            for i in range(1, 10):
                zip_com(os.path.join(d, mes + '-Estabelecimentos%d.zip' % i), [])
            zip_com(os.path.join(d, mes + '-Empresas0.zip'), [
                linha_csv(['11222333', 'JOAO FICTICIO 12345678901', '2135', '50', '1000,00', '01', '']),
                linha_csv(['12121212', 'OFICINA FICTICIA LTDA', '2062', '49', '50000,00', '03', ''])])
            for i in range(1, 10):
                zip_com(os.path.join(d, mes + '-Empresas%d.zip' % i), [])
            zip_com(os.path.join(d, mes + '-Simples.zip'), [linha_csv(['11222333', 'S', '', '', 'N', '', ''])])
            bloq = os.path.join(d, 'nao.txt')
            with open(bloq, 'w') as f:
                f.write('00000000000000\n')
            saida = os.path.join(d, 'leads.csv')
            with mock.patch.object(cli, 'DADOS', d), mock.patch('builtins.print'):
                cli.main(['cidade', '--uf', 'SP', '--municipio', 'Sorocaba', '--mes', mes, '--manter-zips'])
                cli.main(['leads', '--uf', 'SP', '--municipio', 'SOROCABA', '--mes', mes, '--anos-min', '1',
                          '--nao-contatar', bloq, '--saida', saida])
            with open(saida, encoding='utf-8-sig') as f:
                linhas = list(csv.DictReader(f, delimiter=';'))
            nomes = [l['nome'] for l in linhas]
            self.assertEqual(sorted(nomes), ['BARBEARIA DO TESTE', 'OFICINA FICTICIA'])  # nova (<1 ano) fica fora
            self.assertEqual(linhas[0]['nome'], 'BARBEARIA DO TESTE')  # mais pontos primeiro
            self.assertEqual(linhas[1]['sistema_sugerido'], 'MapOS')
            self.assertEqual(linhas[1]['whatsapp'], '')  # fixo não vira link de WhatsApp
            self.assertTrue(all(l['fonte'] == 'Receita Federal, dados abertos CNPJ 2026-10' for l in linhas))
            with open(saida, encoding='utf-8-sig') as f:
                self.assertNotIn('12345678901', f.read())


class TestePlaces(unittest.TestCase):
    def _csv(self, d):
        caminho = os.path.join(d, 'in.csv')
        with open(caminho, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['nome', 'bairro', 'cidade', 'uf'], delimiter=';')
            w.writeheader()
            w.writerow({'nome': 'BARBEARIA DO TESTE', 'bairro': 'CENTRO', 'cidade': 'SOROCABA', 'uf': 'SP'})
            w.writerow({'nome': 'OUTRA', 'bairro': 'CENTRO', 'cidade': 'SOROCABA', 'uf': 'SP'})
        return caminho

    def test_sem_confirmar_nao_chama_a_api(self):
        abrir = mock.Mock()
        with tempfile.TemporaryDirectory() as d:
            n = P.enriquecer(self._csv(d), os.path.join(d, 'out.csv'), 1, abrir=abrir, avisar=lambda *_: None)
        self.assertEqual(n, 0)
        abrir.assert_not_called()

    def test_sem_chave_para(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                P.enriquecer(self._csv(d), os.path.join(d, 'o.csv'), 1, confirmar=True, avisar=lambda *_: None)

    def test_chamada_com_mascara_basica_e_limite(self):
        pedidos = []

        def abrir(req, timeout):
            pedidos.append(req)
            corpo = {'places': [{'id': 'ChIJteste', 'displayName': {'text': 'Barbearia do Teste'},
                                 'googleMapsUri': 'https://maps.google.com/?cid=1', 'businessStatus': 'OPERATIONAL'}]}
            return io.BytesIO(json.dumps(corpo).encode())

        with tempfile.TemporaryDirectory() as d:
            saida = os.path.join(d, 'out.csv')
            n = P.enriquecer(self._csv(d), saida, 1, confirmar=True, chave='chave-falsa', abrir=abrir,
                             avisar=lambda *_: None)
            with open(saida, encoding='utf-8-sig') as f:
                linhas = list(csv.DictReader(f, delimiter=';'))
        self.assertEqual(n, 1)
        self.assertEqual(len(pedidos), 1)  # limite respeitado
        mascara = pedidos[0].get_header('X-goog-fieldmask')
        self.assertNotIn('rating', mascara)  # básico não sobe para o SKU Enterprise
        self.assertEqual(linhas[0]['google_place_id'], 'ChIJteste')
        self.assertEqual(linhas[0]['google_confianca'], 'alta')
        self.assertEqual(linhas[1]['google_place_id'], '')  # fora do limite: intocado


if __name__ == '__main__':
    unittest.main()
