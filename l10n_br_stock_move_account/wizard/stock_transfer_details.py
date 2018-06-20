# -*- coding: utf-8 -*-
# Copyright (C) 2018  Luiz Felipe do Divino - ABGF - luiz.divino@abgf.gov.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    @api.multi
    def do_detailed_transfer(self):
        super(StockTransferDetails, self).do_detailed_transfer()

        if self.company_id.active_stock_move_account:
            self.picking_id.gerar_lancamento_recebimento_definitivo()

        return True
