# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE - Átila Graciano <atilla.silva@kmee.com.br>
# Copyright 2017 KMEE - Bianca Bartolomei <bianca.bartolomei@kmee.com.br>
# Copyright 2017 KMEE - Wagner Pereira <wagner.pereira@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Tabelas SPED Gerais',
    'summary': """
        Implementa as seguintes tabelas do SPED:
	
	EFD/REINF
	Tabela 01 – Códigos de Pagamentos
	Tabela 02 - Regras para utilização dos códigos de pagamento a Pessoas Físicas
	Tabela 03 – Rendimentos de Beneficiários no Exterior
	Tabela 04 - Forma de Tributação para rendimentos de beneficiários no Exterior
	Tabela 05 - Informações sobre os beneficiários de Rendimentos no Exterior
	Tabela 06 – Classificação de Serviços Prestados mediante cessão de mão de obra/Empreitada
	Tabela 07 – Países
	Tabela 08 - Classificação Tributária
	Tabela 09 – Código de Atividades, Produtos e Serviços Sujeitos à CPRB
	Tabela 10 - Eventos da EFD-Reinf

	ESOCIAL
	# TODO - Inserir a lista de tabelas aqui

        """,
    'version': '8.0.0.1.0',
    'category': 'Hidden',
    'license': 'AGPL-3',
    'author': 'ABGF, Agência Brasileira Gestora de Fundos Garantidores e Garantias S.A.',
    'website': 'www.abgf.gov.br',
    'depends': [
        'l10n_br_base',
    ],
    'external_dependencies': {
        'python': [
            'pybrasil',
        ],
    },
    'data': [
        # Segurança
        'security/security.xml',
        'security/ir.model.access.csv',

        # Menu base
        'views/menus.xml',

        # Cadastro de Empresas para Sped
        'views/inherit_sped_empresa.xml',
        'views/lote.xml',

        # Tabelas
        'views/codigo_aliquota_FPAS.xml',
        'views/categoria_trabalhador.xml',
        'views/financiamento_aposentadoria.xml',
        'views/natureza_rubrica.xml',
        'views/parte_corpo.xml',
        'views/tipo_inscricao.xml',
        'views/agente_causador.xml',
        'views/situacao_geradora_doenca.xml',
        'views/situacao_geradora_acidente.xml',
        'views/natureza_lesao.xml',
        'views/tipo_dependente.xml',
        'views/tipo_lotacao_tributaria.xml',
        'views/motivo_afastamento.xml',
        'views/tipo_arquivo_esocial.xml',
        'views/motivo_desligamento.xml',
        'views/tipo_logradouro.xml',
        'views/natureza_juridica.xml',
        'views/motivo_cessacao.xml',
        'views/tipo_beneficio.xml',
        'views/codificacao_acidente_trabalho.xml',
        'views/fatores_meio_ambiente.xml',
        'data/classificacao_tributaria.xml',
        'data/natureza_lesao.xml',
        'data/tipo_arquivo_esocial.xml',
        'data/tipo_lotacao_tributaria.xml',
        'data/categoria_trabalhador.xml',
        'data/financiamento_aposentadoria.xml',
        'data/natureza_rubrica.xml',
        'data/tipo_dependente.xml',
        'data/parte_corpo.xml',
        'data/tipo_inscricao.xml',
        'data/agente_causador.xml',
        'data/situacao_geradora_doenca.xml',
        'data/situacao_geradora_acidente.xml',
        'data/natureza_lesao.xml',
        'data/motivo_afastamento.xml',
        'data/motivo_desligamento.xml',
        'data/tipo_logradouro.xml',
        'data/natureza_juridica.xml',
        'data/motivo_cessacao.xml',
        'data/tipo_beneficio.xml',
        'data/codificacao_acidente_trabalho.xml',
        'data/fatores_meio_ambiente.xml',
        'data/codigo_aliquota_FPAS.xml',
    ],
    'application': True,
}
