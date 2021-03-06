# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATIDA LTDA
#   Aristides Caldeira <aristides.caldeira@kmee.com.br>
#   Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models


class SpedAccountMoveTemplate(models.Model):
    _name = b'sped.account.move.template'
    _description = 'Modelo de partidas dobradas'
    _rec_name = 'nome'

    nome = fields.Char(
        string='Descrição',
        required=True,
        index=True,
    )
    parent_id = fields.Many2one(
        comodel_name='sped.account.move.template',
        string='Modelo superior',
    )
    child_ids = fields.One2many(
        comodel_name='sped.account.move.template',
        inverse_name='parent_id',
        string='Modelos subordinados'
    )
    # operacao_ids = fields.Many2many(
    #     comodel_name='sped.operacao',
    #     relation='sped_account_move_template_operacao',
    #     column1='template_id',
    #     column2='operacao_id',
    #     string='Operações Fiscais',
    # )
    item_ids = fields.One2many(
        comodel_name='sped.account.move.template.item',
        inverse_name='template_id',
        string='Itens',
    )
    fiscal_category_ids = fields.One2many(
        comodel_name='l10n_br_account.fiscal.category',
        inverse_name='account_move_template_id',
        string='Categorias Fiscais Relacionadas'
    )

    # @api.constrains('operacao_ids')
    # def _constraints_operacao_ids(self):
    #     for operacao in self.operacao_ids:
    #         if len(operacao.account_move_template_ids) > 1:
    #             raise UserError(u'A operação fiscal %s já tem um
    # modelo de partidas dobradas vinculado!' % operacao.nome)
