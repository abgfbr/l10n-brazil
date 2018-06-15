# -*- coding: utf-8 -*-
# Copyright (C) 2018  Luiz Felipe do Divino - ABGF - luiz.divino@abgf.gov.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models, fields
from openerp.exceptions import Warning
from openerp.addons.l10n_br_account_product.constantes import \
    ACCOUNT_AUTOMATICO_PRODUTO


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _get_period(self):
        return self.env['account.move']._get_period()

    state = fields.Selection(
        selection_add=[('provisorio', 'Recebimento Provisório')]
    )

    journal_id = fields.Many2one(
        string='Diário',
        comodel_name='account.journal',
    )

    period_id = fields.Many2one(
        string='Periodo',
        comodel_name='account.period',
        default=_get_period
    )

    temporary_move_id = fields.Many2one(
        string='Movimentações Contábeis Temporário',
        comodel_name='account.move',
        ondelete='restrict'
    )

    definitive_move_id = fields.Many2one(
        string='Movimentações Contábeis Definitivo',
        comodel_name='account.move',
        ondelete='restrict'
    )

    @api.multi
    def action_confirm(self):
        stock_id = super(StockPicking, self).action_confirm()

        if self.company_id.temporary_account_journal_id:
            self.journal_id = self.company_id.temporary_account_journal_id.id

        self.gera_movimentacao_contabil_transitoria()

        return stock_id

    @api.multi
    def action_provisorio(self):
        for line in self.move_lines:
            line.state = 'provisorio'

        return True

    @api.multi
    def _state_get(self, field_name, arg):
        res = {}

        if all([x.state == 'provisorio' for x in self.move_lines]):
            res[self.id] = 'provisorio'
            return res

        return super(StockPicking, self)._state_get(field_name, arg)

    @api.depends('code', 'state')
    def get_status(self):
        is_draft = False
        is_incoming = False
        is_done = False

        if self.state == 'draft':
            is_draft = True
        elif self.state == 'provisorio':
            is_done = True
        if self.code == 'incoming':
            is_incoming = True
        self.status = (is_incoming and not is_done) or \
                      (is_draft and not is_incoming)

    @api.multi
    def _validar_tipo_picking(self):
        if self.code != 'incoming':
            return False

        if self.company_id.active_stock_move_account:
            self._validar_configuracoes_movimentacao_transitoria(
                self.company_id.account_move_template_id
            )
        else:
            return False

        return True

    @api.multi
    def gera_movimentacao_contabil_transitoria(self):
        for stock in self:
            if stock._validar_tipo_picking():
                move_template = self.company_id.account_move_template_id
                account_move_lines = []

                self.gera_account_move_line(
                    account_move_lines, move_template, stock
                )

                if account_move_lines:
                    move_vals = stock.get_account_move_stock_vals(
                        account_move_lines
                    )

                    move = self.env['account.move'].create(move_vals)

                    stock.temporary_move_id = move

    def get_account_move_stock_vals(self, account_move_lines):
        move_vals = {
            'ref': self.name,
            'line_id': account_move_lines,
            'journal_id': self.journal_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date,
            'company_id': self.company_id.id,
        }
        return move_vals

    @api.multi
    def gera_account_move_line(self, account_move_lines, move_template, stock):
        for line in stock.move_lines:
            self._gerar_linhas_transicao_temporaria(
                account_move_lines, line, move_template
            )

    @api.multi
    def _gerar_linhas_transicao_temporaria(self, account_move_lines, line,
                                           move_template):
        for template_item in move_template.item_ids:
            if not getattr(line, template_item.campo, False):
                continue

            valor_produto = line.purchase_line_id.price_unit if \
                line.purchase_line_id else line.product_id.standard_price
            quantidade_produto = line.product_uom_qty
            valor_total = valor_produto * quantidade_produto

            account_debito = None
            if template_item.account_debito_id:
                account_debito = template_item.account_debito_id
            elif template_item.account_automatico_debito == \
                    ACCOUNT_AUTOMATICO_PRODUTO:
                product = line.product_id
                account_debito = product.property_account_income

            if account_debito is not None:
                dados = {
                    'account_id': account_debito.id,
                    'name': line.product_id.name,
                    'narration': template_item.campo,
                    'debit': valor_total,
                    'partner_id': line.picking_id.partner_id.id,
                }
                account_move_lines.append((0, 0, dados))

            account_credito = None
            if template_item.account_credito_id:
                account_credito = template_item.account_credito_id

            elif template_item.account_automatico_credito == \
                    ACCOUNT_AUTOMATICO_PRODUTO:
                product = line.product_id
                account_credito = product.property_account_expense

            if account_credito is not None:
                dados = {
                    'account_id': account_credito.id,
                    'name': line.product_id.name,
                    'narration': template_item.campo,
                    'credit': valor_total,
                    'partner_id': line.picking_id.partner_id.id,
                }
                account_move_lines.append((0, 0, dados))

    def _validar_configuracoes_movimentacao_transitoria(
            self, move_template):
        if not move_template:
            raise Warning(
                'É necessário escolher um modelo de partida dobrada '
                'para gerar a movimentação temporária!'
            )
        if not self.journal_id:
            raise Warning(
                'É necessário escolher um diário para gerar a '
                'movimentação temporária!'
            )
        if not self.period_id:
            raise Warning(
                'É necessário escolher o periodo de vigencia para '
                'gerar a movimentação temporária!'
            )

    @api.multi
    def gerar_lancamento_recebimento_definitivo(self):
        for stock in self:
            if stock._validar_tipo_picking():
                if stock.temporary_move_id:
                    account_move_lines = []
                    for line in stock.temporary_move_id.line_id:
                        if line.debit:
                            dados = {
                                'account_id': line.account_id.id,
                                'name': line.name,
                                'narration': 'teste',
                                'credit': line.debit,
                                'partner_id': line.partner_id.id,
                            }
                            account_move_lines.append((0, 0, dados))

                        if line.credit:
                            product_id = self.env['product.product'].search(
                                [('name', '=', line.name)]
                            )
                            if not product_id.property_account_expense:
                                raise Warning(
                                    'É preciso configurar as contas de '
                                    'despesa/receita do(s) produto(s)!'
                                )
                            dados = {
                                'account_id':
                                    product_id.property_account_expense.id,
                                'name': line.name,
                                'narration': 'teste',
                                'debit': line.credit,
                                'partner_id': line.partner_id.id,
                            }
                            account_move_lines.append((0, 0, dados))

                    if account_move_lines:
                        move_vals = stock.get_account_move_stock_vals(
                            account_move_lines
                        )

                        move = self.env['account.move'].create(move_vals)

                        stock.definitive_move_id = move


class StockMove(models.Model):
    _inherit = 'stock.move'

    state = fields.Selection(
        selection_add=[('provisorio', 'Recebimento Provisório')]
    )
