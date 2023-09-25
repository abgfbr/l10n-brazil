# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions


class SpedReinfAccountInvoice(models.Model):
    _inherit = "account.invoice"

    data_pagamento = fields.Date(
        string="Data do Pagamento",
    )
