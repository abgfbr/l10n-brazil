# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

{
    'name': 'SPED - NF-e / NFC-e',
    'version': '11.0.1.0.0',
    'author': 'Odoo Community Association (OCA), Ari Caldeira',
    'category': 'Base',
    'depends': [
        'l10n_br_base',
        'sped_imposto',
        'sped',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'data': [
        'views/sped_certificado_view.xml',
        'views/inherited_sped_empresa_view.xml',
        'views/inherited_sped_documento_emissao_nfe_view.xml',
        'views/inherited_sped_documento_emissao_nfce_view.xml',
        'views/sped_documento_carta_correcao_view.xml',
        'views/sped_consulta_dfe_view.xml',
        'views/sped_importa_nfe.xml',
    ],
    'external_dependencies': {
        'python': ['pybrasil', 'pysped', 'mako'],
    }
}
