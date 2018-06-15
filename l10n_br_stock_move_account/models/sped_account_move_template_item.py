# -*- coding: utf-8 -*-
# Copyright (C) 2018  Luiz Felipe do Divino - ABGF - luiz.divino@abgf.gov.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models, fields
from openerp.addons.l10n_br_account_product.constantes import \
    CAMPO_DOCUMENTO_FISCAL

CAMPO_DOCUMENTO_FISCAL.append(('product_id', 'Produto'))
