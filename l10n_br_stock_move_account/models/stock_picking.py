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
        return self.env['account.period'].find()

    state = fields.Selection(
        selection_add=[
            ('provisorio', 'Recebimento Provisório'),
        ]
    )

    temporary_journal_id = fields.Many2one(
        string='Diário Recebimento Provisório',
        comodel_name='account.journal',
    )

    definitive_journal_id = fields.Many2one(
        string='Diário Recebimento Definitivo',
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
    )

    definitive_move_id = fields.Many2one(
        string='Movimentações Contábeis Definitivo',
        comodel_name='account.move',
    )

    historic_temporary_move = fields.Text(
        string='Histórico Lançamento Temporário',
    )

    historic_definitive_move = fields.Text(
        string='Histórico Lançamento Definitivo',
    )

    gerar_contabilizacao = fields.Boolean(
        string='Gerar Contabilização',
        compute='_compute_verificar_contabilizacao',
    )

    @api.multi
    @api.depends('period_id')
    def _compute_verificar_contabilizacao(self):
        for record in self:
            record.gerar_contabilizacao = \
                record.company_id.active_stock_move_account

    @api.multi
    def action_provisorio(self):
        if self.company_id.temporary_account_journal_id:
            self.gera_movimentacao_contabil_transitoria()

        self.env.cr.execute(
            "update stock_picking set state='provisorio' where id=%d" % self.id
        )

    @api.multi
    def _validar_tipo_picking(self, journal_id):
        if self.picking_type_code != 'incoming':
            return False

        if not self.company_id.active_stock_move_account:
            return False

        self._validar_configuracoes_movimentacao_transitoria(
            self.company_id.account_move_template_id, journal_id
        )

        return True

    @api.multi
    def gera_movimentacao_contabil_transitoria(self):
        for stock in self:
            if not stock.temporary_journal_id:
                stock.temporary_journal_id = \
                    stock.company_id.temporary_account_journal_id.id

            if stock._validar_tipo_picking(stock.temporary_journal_id):
                move_template = stock.company_id.account_move_template_id
                account_move_lines = []

                stock.gera_account_move_line(
                    account_move_lines, move_template
                )

                if account_move_lines:
                    move_vals = stock.get_account_move_stock_vals(
                        account_move_lines, stock.temporary_journal_id,
                        stock.historic_temporary_move
                    )

                    move = self.env['account.move'].create(move_vals)

                    stock.temporary_move_id = move

    def get_account_move_stock_vals(
            self, account_move_lines, journal_id, historico_lancamento):
        move_vals = {
            'ref': self.name,
            'line_id': account_move_lines,
            'journal_id': journal_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date,
            'company_id': self.company_id.id,
            'narration': historico_lancamento,
        }
        return move_vals

    @api.multi
    def gera_account_move_line(self, account_move_lines, move_template):
        for line in self.move_lines:
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
            self, move_template, journal_id):
        if not move_template:
            raise Warning(
                'É necessário escolher um modelo de partida dobrada '
                'para gerar a movimentação temporária!'
            )
        if not journal_id:
            raise Warning(
                'É necessário escolher os diários para gerar a '
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
            if not stock.temporary_move_id:
                return

            if not self.definitive_journal_id:
                self.definitive_journal_id = \
                    self.company_id.definitive_account_journal_id.id

            if stock._validar_tipo_picking(self.definitive_journal_id):
                template_id = \
                    stock.company_id.account_move_definitive_template_id
                account_move_lines = []

                for line in stock.temporary_move_id.line_id:
                    for template_item in template_id.item_ids:
                        account_debito = None
                        if template_item.account_debito_id:
                            account_debito = template_item.account_debito_id
                        elif template_item.account_automatico_debito == \
                                ACCOUNT_AUTOMATICO_PRODUTO:
                            product = line.product_id
                            account_debito = product.property_account_income

                        if account_debito and line.credit:
                            dados = {
                                'account_id': account_debito.id,
                                'name': line.name,
                                'debit': line.credit,
                                'partner_id': line.partner_id.id,
                            }
                            account_move_lines.append((0, 0, dados))

                        account_credito = None
                        if template_item.account_credito_id:
                            account_credito = \
                                template_item.account_credito_id

                        elif template_item.account_automatico_credito == \
                                ACCOUNT_AUTOMATICO_PRODUTO:
                            product = self.env['product.product'].search(
                                [('name', '=', line.name)]
                            )

                            if not product.property_account_expense:
                                raise Warning(
                                    'É preciso configurar as contas de '
                                    'despesa/receita do(s) produto(s)!'
                                )
                            account_credito = \
                                product.property_account_expense

                        if account_credito and line.debit:
                            dados = {
                                'account_id': account_credito.id,
                                'name': line.name,
                                'credit': line.debit,
                                'partner_id': line.partner_id.id,
                            }
                            account_move_lines.append((0, 0, dados))

                if account_move_lines:
                    move_vals = stock.get_account_move_stock_vals(
                        account_move_lines, stock.definitive_journal_id,
                        stock.historic_definitive_move
                    )

                    move = self.env['account.move'].create(move_vals)

                    stock.definitive_move_id = move
