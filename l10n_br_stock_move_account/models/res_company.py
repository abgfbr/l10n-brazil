# -*- coding: utf-8 -*-
# Copyright (C) 2018  Luiz Felipe do Divino - ABGF - luiz.divino@abgf.gov.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    active_stock_move_account = fields.Boolean(
        string='Lançamentos Contábeis Movimentações Estoque',
        default=False
    )

    account_move_template_id = fields.Many2one(
        string='Modelo de partida dobrada',
        comodel_name='sped.account.move.template'
    )
    
    temporary_account_journal_id = fields.Many2one(
        string='Diário Padrão',
        comodel_name='account.journal'
    )
