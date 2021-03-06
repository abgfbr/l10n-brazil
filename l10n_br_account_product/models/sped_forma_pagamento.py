# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models

from ..constantes import (
    FORMA_PAGAMENTO,
    FORMA_PAGAMENTO_OUTROS,
    BANDEIRA_CARTAO,
    INTEGRACAO_CARTAO,
    INTEGRACAO_CARTAO_NAO_INTEGRADO,
)

class SpedFormaPagamento(models.Model):
    """ Visando atendar o layout da nf-e 4.0 e também do SAT implementamos
    a forma de pagamento associada ao account.payment.term e consideramos
    o payment.mode como a CARTEIRA.

    Portanto:

    account.payment.term:
        - [Boleto] 5x sem juros
        - [Cartão de Crédito] 12x sem juros

    sped.forma.pagamento:
        - Boleto
        - Cheque
        - Cartão de crédito
        - Dinheiro

    payment.mode:
        - Boleto Bradesco Carteira 123
        - Boleto Bradesco Carteira 222

    payment.mode.type:
        - Cobrança CNAB 240
        - Cobrança CNAB 400

    """
    _name = b'sped.forma.pagamento'
    _description = 'Forma de Pagamento'

    name = fields.Char(
        string="Nome",
        required=True,
    )
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento',
        default=FORMA_PAGAMENTO_OUTROS,
        required=True,
    )
    bandeira_cartao = fields.Selection(
        selection=BANDEIRA_CARTAO,
        string='Bandeira do cartão',
    )
    integracao_cartao = fields.Selection(
        selection=INTEGRACAO_CARTAO,
        string='Integração do cartão',
        default=INTEGRACAO_CARTAO_NAO_INTEGRADO,
    )
    payment_term_id = fields.One2many(
        comodel_name='account.payment.term',
        inverse_name='sped_forma_pagamento_id',
        string='Condições de pagamento',
    )
