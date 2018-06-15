# -*- coding: utf-8 -*-
# Copyright (C) 2018  Luiz Felipe do Divino - ABGF - luiz.divino@abgf.gov.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localization Warehouse Operations Accounting',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'ABGF, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_br_stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/stock_picking_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
