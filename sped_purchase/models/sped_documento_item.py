# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SpedDocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    purchase_line_ids = fields.Many2many(
        string='Linha do pedido',
        comodel_name='purchase.order.line',
        copy=False,
    )

    purchase_ids = fields.Many2many(
        string='Pedido de compra',
        comodel_name='purchase.order',
        copy=False,
    )

    pode_alterar_quantidade = fields.Boolean(
        string='Pode alterar a quantidade?',
        compute='_compute_quantidade_alteravel',
        default=True,
    )

    def faturar_linhas(self):
        for linha in self.mapped('purchase_line_ids'):
            total = 0.0
            for qty in linha.documento_item_ids.mapped('quantidade'):
                total += qty
            linha.qty_invoiced = total

    def executa_depois_create(self):
        for item in self:
            data = {
                'produto_id': item.produto_id,
                'quantidade': item.quantidade,
                'vr_unitario': item.vr_unitario,
                'vr_frete': item.vr_frete,
                'vr_seguro': item.vr_seguro,
                'vr_desconto': item.vr_desconto,
                'vr_outras': item.vr_outras,
            }
            for linha in item.purchase_ids.mapped('order_line') - \
                    item.mapped('purchase_line_ids'):
                if all(linha[field] == data[field] for field in data.keys()):
                    item.purchase_line_ids += linha

    @api.onchange('purchase_ids', 'purchase_line_ids')
    def _onchange_purchase_line_ids(self):
        result = {}


        result['domain'] = {'purchase_line_ids': [
            ('id', 'in', purchase_line_ids.ids),
            ('id', 'not in', self.purchase_line_ids.ids),
        ], 'purchase_ids': [
            ('invoice_status', '=', 'to invoice'),
            ('id', 'not in', self.purchase_ids.ids),
        ]}

        if self.partner_id:
            result['domain']['purchase_line_ids'].append(
                ('partner_id', '=', self.partner_id.id)
            )
            result['domain']['purchase_ids'].append(
                ('partner_id', '=', self.partner_id.id)
            )

        if self.empresa_id:
            result['domain']['purchase_line_ids'].append(
                ('empresa_id', '=', self.empresa_id.id)
            )
            result['domain']['purchase_ids'].append(
                ('empresa_id', '=', self.empresa_id.id)
            )

        if self.produto_id:
            result['domain']['purchase_line_ids'].append(
                ('produto_id', '=', self.produto_id.id)
            )

        if self.vr_unitario:
            result['domain']['purchase_line_ids'].append(
                ('vr_unitario', '=', self.vr_unitario)
            )

        return result

    @api.constrains('purchase_line_ids', 'quantidade')
    def _check_m2m_quantity(self):
        for item in self:
            if len(item.purchase_line_ids) > 1:
                for linha in item.mapped('purchase_line_ids'):
                    if len(linha.documento_item_ids) > 1:
                        raise ValidationError(_(
                            'Impossível relacionar item de documento com '
                            'linhas de pedido de compras que não tenham '
                            'relação única com esse item.'
                        ))
            elif item.purchase_line_ids:
                total = 0.0
                for doc_item in item.purchase_line_ids.mapped(
                        'documento_item_ids'):
                    total += doc_item.quantidade
                if total > item.purchase_line_ids.quantidade:
                    raise ValidationError(_(
                        'Quantidade do produto ' + item.produto_id.nome +
                        'ultrapassa o disponível na linha do pedido de compra.'
                    ))

    @api.depends('purchase_line_ids')
    def _compute_quantidade_alteravel(self):
        for item in self:
            if len(item.purchase_line_ids) > 1:
                item.pode_alterar_quantidade = False
                quantidade = 0.0
                for linha in item.mapped('purchase_line_ids'):
                    quantidade += linha.quantidade
                item.quantidade = quantidade
            else:
                item.pode_alterar_quantidade = True
