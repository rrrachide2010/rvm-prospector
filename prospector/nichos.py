"""Nichos de prospecção: CNAE da Receita -> sistema do Kit Proibido -> dor que o cliente fala.

Os códigos são subclasses CNAE de 7 dígitos, conferidos na tabela Cnaes.zip da Receita (base 2026-10).
A tabela "Para quem vender cada sistema" do Kit Proibido é a origem dos pares nicho/sistema/dor.
`prospector nichos --conferir` confere todos os códigos contra a tabela da Receita baixada.

Setores agrupam nichos: `--nichos saude` traz todo o universo da saúde (consultórios, clínicas, laboratórios,
farmácias, lojas cirúrgicas, fisioterapia, nutrição etc.). Fora de propósito: veterinária, planos de saúde e
indústria farmacêutica (o cliente é outro).
"""

NICHOS = {
    'beleza': {
        'nome': 'Barbearia, salão, estética',
        'cnaes': ['9602501', '9602502'],
        'sistema': 'Easy!Appointments',
        'dor': 'Perco cliente que manda mensagem e eu não respondo a tempo.',
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


# --------------------------------------------------------------------------------------------- saúde
# Universo da saúde (pedido do João em 21/10/2026). Contagem de estabelecimentos ativos em Sorocaba,
# base 2026-10, só CNAE principal, entre parênteses, para dar ordem de grandeza.
SAUDE = {
    'medico': {
        'nome': 'Saúde: clínica médica, consultório',
        # consultas (1558), com cirurgia (201), com exames (226), vacinação, reprodução, outras ambulatoriais
        'cnaes': ['8630503', '8630501', '8630502', '8630506', '8630507', '8630599'],
        'sistema': 'Easy!Appointments (agenda online) + Chatwoot (WhatsApp da recepção)',
        'dor': 'Paciente falta na consulta e a recepção não dá conta do WhatsApp.',
    },
    'odonto': {
        'nome': 'Saúde: odontologia, prótese dentária',
        'cnaes': ['8630504', '8630505', '3250706'],
        'sistema': 'Easy!Appointments + Chatwoot',
        'dor': 'O orçamento do tratamento sai e o paciente não volta para fechar.',
    },
    'laboratorio': {
        'nome': 'Saúde: laboratório de análises',
        'cnaes': ['8640202', '8640201'],
        'sistema': 'Chatwoot (atendimento e aviso de resultado)',
        'dor': 'Paciente liga o dia todo para saber se o resultado saiu.',
    },
    'diagnostico': {
        'nome': 'Saúde: imagem, diagnóstico e terapia especializada',
        'cnaes': ['8640204', '8640205', '8640206', '8640207', '8640208', '8640209', '8640203', '8640210',
                  '8640211', '8640212', '8640213', '8640214', '8640299'],
        'sistema': 'Easy!Appointments + Chatwoot',
        'dor': 'Paciente chega sem o preparo do exame ou falta, e o horário do aparelho fica vazio.',
    },
    'fisioterapia': {
        'nome': 'Saúde: fisioterapia, terapia ocupacional',
        'cnaes': ['8650004', '8650005'],
        'sistema': 'Easy!Appointments (pacote de sessões) + Chatwoot',
        'dor': 'O paciente some no meio do pacote de sessões.',
    },
    'nutricao': {
        'nome': 'Saúde: nutrição',
        'cnaes': ['8650002', '8650007'],
        'sistema': 'Easy!Appointments + Chatwoot',
        'dor': 'O paciente não volta para o retorno.',
    },
    'psicologia': {
        'nome': 'Saúde: psicologia, saúde mental',
        'cnaes': ['8650003', '8720401', '8720499'],
        'sistema': 'Easy!Appointments',
        'dor': 'Remarcar e cobrar sessão por mensagem toma o dia.',
    },
    'fonoaudiologia': {
        'nome': 'Saúde: fonoaudiologia',
        'cnaes': ['8650006'],
        'sistema': 'Easy!Appointments + Chatwoot',
        'dor': 'Agenda de terapia semanal remarcada à mão, paciente por paciente.',
    },
    'enfermagem': {
        'nome': 'Saúde: enfermagem, home care, remoção',
        'cnaes': ['8712300', '8650001', '8621601', '8621602', '8622400'],
        'sistema': 'Chatwoot + Nextcloud (escala e prontuário de visita)',
        'dor': 'Escala de cuidadores e plantões vive em grupo de WhatsApp.',
    },
    'integrativas': {
        'nome': 'Saúde: práticas integrativas, acupuntura, podologia e outros',
        'cnaes': ['8690901', '8690903', '8690904', '8690902', '8690999', '8650099', '8660700'],
        'sistema': 'Easy!Appointments',
        'dor': 'Cliente manda mensagem para marcar e eu respondo só no fim do dia.',
    },
    'hospital': {
        'nome': 'Saúde: hospital, pronto atendimento',
        'cnaes': ['8610101', '8610102'],
        'sistema': 'Chatwoot (central de atendimento)',
        'dor': 'Paciente e família ligam e ninguém sabe quem respondeu o quê.',
    },
    'farmacia': {
        'nome': 'Saúde: farmácia, manipulação',
        'cnaes': ['4771701', '4771702', '4771703'],
        'sistema': 'Chatwoot (orçamento no WhatsApp) + Odoo Community (estoque)',
        'dor': 'Cliente pede orçamento de remédio ou fórmula no WhatsApp e desiste porque demora.',
    },
    'artigos_medicos': {
        'nome': 'Saúde: loja cirúrgica, ortopédica, aluguel de equipamentos',
        'cnaes': ['4773300', '7729203', '7739002'],
        'sistema': 'Dolibarr ou Odoo Community (estoque e locação)',
        'dor': 'Aluguel de cadeira e cama hospitalar controlado em caderno: não sei o que está na rua.',
    },
    'distribuidora_saude': {
        'nome': 'Saúde: distribuidora, representante, manutenção de equipamentos',
        'cnaes': ['4645101', '4645102', '4645103', '4644301', '4664800', '4618401', '4618402', '3312103'],
        'sistema': 'Krayin CRM (pedidos e visitas) ou Odoo Community',
        'dor': 'Pedido de clínica chega por WhatsApp e se perde entre um vendedor e outro.',
    },
    'otica': {
        'nome': 'Saúde: ótica',
        'cnaes': ['4774100', '3250707', '3250709'],
        'sistema': 'Dolibarr (ordem de serviço do óculos) + Chatwoot',
        'dor': 'O óculos fica pronto e o cliente não é avisado; a receita vence e ele não volta.',
    },
    'idosos': {
        'nome': 'Saúde: residência geriátrica, cuidado continuado',
        'cnaes': ['8711501', '8711502', '8711503', '8711504', '8711505'],
        'sistema': 'Chatwoot (família) + Nextcloud (registros)',
        'dor': 'A família pede notícia o dia todo por mensagem.',
    },
    'academia': {
        'nome': 'Saúde: academia, estúdio de condicionamento físico',
        'cnaes': ['9313100'],
        'sistema': 'Easy!Appointments (aulas e avaliações) + Chatwoot',
        'dor': 'Aluno some depois do segundo mês e ninguém percebe a tempo.',
    },
}
NICHOS.update(SAUDE)

SETORES = {
    'saude': list(SAUDE),
}

def expandir(chaves):
    """Troca setor pelos nichos dele ('saude' -> medico, odonto, ...), sem repetir e na ordem pedida."""
    saida = []
    for chave in chaves:
        for k in SETORES.get(chave, [chave]):
            if k not in saida:
                saida.append(k)
    return saida


def setor_de(chave):
    return next((s for s, ks in SETORES.items() if chave in ks), '')


def cnae_para_nicho(chaves=None):
    """{cnae: chave_do_nicho} para os nichos ou setores pedidos (todos, se None). Um CNAE pertence a um nicho só."""
    chaves = expandir([c.strip() for c in chaves if c.strip()]) if chaves else list(NICHOS)
    mapa = {}
    for chave in chaves:
        if chave not in NICHOS:
            raise ValueError('nicho desconhecido: %s (use: %s, ou o setor: %s)' % (chave, ', '.join(NICHOS), ', '.join(SETORES)))
        for c in NICHOS[chave]['cnaes']:
            mapa[c] = chave
    return mapa
