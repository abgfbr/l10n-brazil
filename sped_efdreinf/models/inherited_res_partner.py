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

    inf_relativas_rendimento = fields.Many2one(
        string=u"Informações relativas ao rendimento no exterior",
        comodel_name="sped.informacoes.relativas.exterior",
    )

    trib_rendimentos_exterior = fields.Many2one(
        string=u"Tributação dos rendimentos no exterior",
        comodel_name="sped.tributacao.rendimentos.exterior",
    )

    ind_nif = fields.Selection(
        string="Indicativo NIF",
        selection=[
            ("1", "Beneficiário com NIF"),
            ("2", "Beneficiário dispensado do NIF"),
            ("3", "País não exige NIF"),
        ],
    )

    nif = fields.Integer(
        string="NIF",
    )
