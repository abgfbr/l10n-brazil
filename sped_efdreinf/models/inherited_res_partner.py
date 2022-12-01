# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions


class ResPartner(models.Model):
    _inherit = "res.partner"

    reinf_natureza_remuneracao_id = fields.Many2one(
        string=u"Reinf - Natureza da remuneração",
        comodel_name="sped.reinf.natureza.rendimentos",
    )
