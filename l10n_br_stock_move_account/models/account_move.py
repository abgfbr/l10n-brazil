# -*- coding: utf-8 -*-
# Copyright (C) 2018  Luiz Felipe do Divino - ABGF - luiz.divino@abgf.gov.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_id = fields.Many2one(
        string='Movimentação de Estoque',
        comodel_name='stock.picking'
    )
