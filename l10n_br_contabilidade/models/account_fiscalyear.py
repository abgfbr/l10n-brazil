# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscalyear'

    sequence_id = fields.Many2one(
        'ir.sequence',
        string=u'Sequence',
        readonly=True,
    )