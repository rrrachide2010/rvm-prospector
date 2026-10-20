"""Nichos de prospecção: CNAE da Receita -> sistema do Kit Proibido -> dor que o cliente fala.

Os códigos são subclasses CNAE de 7 dígitos, conferidos na tabela Cnaes.zip da Receita (base 2026-10).
A tabela "Para quem vender cada sistema" do Kit Proibido é a origem dos pares nicho/sistema/dor.
`prospector nichos --conferir` confere todos os códigos contra a tabela da Receita baixada.
"""

NICHOS = {
    'beleza': {
        'nome': 'Barbearia, salão, estética',
        'cnaes': ['9602501', '9602502'],
        'sistema': 'Easy!Appointments',
        'dor': 'Perco cliente que manda mensagem e eu não respondo a tempo.',
    },
    'saude': {
        'nome': 'Clínica, consultório',
        'cnaes': ['8630503', '8630504', '8650004', '8650003', '8650006', '8690901'],
        'sistema': 'Chatwoot + Easy!Appointments',
        'dor': 'A recepção não dá conta do WhatsApp.',
    },
    'assistencia': {
        'nome': 'Assistência técnica, oficina',
        'cnaes': ['9511800', '9512600', '9521500', '4520001', '4520002', '4520003'],
        'sistema': 'MapOS',
        'dor': 'Não sei quais aparelhos estão parados nem quanto tenho a receber.',
    },
    'alimentacao': {
        'nome': 'Restaurante, lanchonete',
        'cnaes': ['5611201', '5611203', '5620104'],
        'sistema': 'TastyIgniter',
        'dor': 'O app de entrega fica com uma parte grande do pedido.',
    },
    'hospedagem': {
        'nome': 'Pousada, hotel pequeno',
        'cnaes': ['5510801', '5590601', '5590603', '5590699'],
        'sistema': 'QloApps',
        'dor': 'Reserva chega por mensagem e eu anoto no caderno.',
    },
    'comercio': {
        'nome': 'Pequeno comércio, distribuidora',
        'cnaes': ['4744099', '4744001', '4723700', '4635402', '4635499', '4712100'],
        'sistema': 'Dolibarr ou Odoo Community',
        'dor': 'Estoque em planilha não bate.',
    },
    'vendas': {
        'nome': 'Imobiliária, equipe de vendas',
        'cnaes': ['6821801', '6821802', '6822600'],
        'sistema': 'Krayin CRM',
        'dor': 'Lead se perde entre um vendedor e outro.',
    },
    'ensino': {
        'nome': 'Escola, treinamento',
        'cnaes': ['8599604', '8593700', '8599603', '8599605', '8599699'],
        'sistema': 'Moodle',
        'dor': 'Curso fica espalhado em grupo de WhatsApp.',
    },
    'escritorio': {
        'nome': 'Escritório (contábil, advocacia)',
        'cnaes': ['6920601', '6920602', '6911701'],
        'sistema': 'Nextcloud',
        'dor': 'Arquivo do cliente em pen drive e e-mail.',
    },
}


def cnae_para_nicho(chaves=None):
    """{cnae: chave_do_nicho} para os nichos pedidos (todos, se None). Um CNAE pertence a um nicho só."""
    chaves = chaves or list(NICHOS)
    mapa = {}
    for chave in chaves:
        if chave not in NICHOS:
            raise ValueError('nicho desconhecido: %s (use: %s)' % (chave, ', '.join(NICHOS)))
        for c in NICHOS[chave]['cnaes']:
            mapa[c] = chave
    return mapa
