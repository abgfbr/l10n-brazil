# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields
from openerp.addons import decimal_precision as dp

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT,
    NFE_IND_IE_DEST,
    NFE_IND_IE_DEST_DEFAULT,
)


FISCAL_CATEGORY_PURPOSE = [
    ('1', 'Normal'),
    ('2', 'Complementar'),
    ('3', 'Ajuste'),
    ('4', u'Devolução de Mercadoria')]

class L10nBrAccountFiscalCategory(models.Model):
    _inherit = 'l10n_br_account.fiscal.category'

    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', required=True,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)

    purpose = fields.Selection(FISCAL_CATEGORY_PURPOSE, u'Finalidade')

    financial_document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Tipo de documento',
        ondelete='restrict',
    )
    financial_account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Conta financeira',
        ondelete='restrict',
        domain=[('type', '=', 'A')],
    )
    account_move_template_id = fields.Many2one(
        comodel_name='sped.account.move.template',
        string='Modelo de partida dobrada',
    )
    payment_term_required = fields.Boolean(
        string=u'Condição de pagamento obrigatória'
    )


class L10nBrAccountDocumentSerie(models.Model):
    _inherit = 'l10n_br_account.document.serie'

    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', required=True,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)


class L10nBrAccountPartnerFiscalType(models.Model):
    _inherit = 'l10n_br_account.partner.fiscal.type'

    ind_ie_dest = fields.Selection(
        NFE_IND_IE_DEST,
        u'Contribuinte do ICMS',
        required=True,
        default=NFE_IND_IE_DEST_DEFAULT
    )
    issqn_wh = fields.Boolean(u'Retém ISSQN')
    inss_wh = fields.Boolean(u'Retém INSS')
    pis_wh = fields.Boolean(u'Retém PIS')
    cofins_wh = fields.Boolean(u'Retém COFINS')
    csll_wh = fields.Boolean(u'Retém CSLL')
    irrf_wh = fields.Boolean(u'Retém IRRF')
    irrf_wh_percent = fields.Float(u'Retenção de IRRF (%)',
                                   digits_compute=dp.get_precision('Discount'))
