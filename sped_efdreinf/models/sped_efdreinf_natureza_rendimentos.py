# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions


class SpedReinfNaturezaRendimentos(models.Model):
    _name = "sped.reinf.natureza.rendimentos"

    name = fields.Char(
        string="Name",
        compute="_compute_name",
    )

    codigo = fields.Char(
        string="Código",
        required=True,
    )
    natureza_rendimento = fields.Char(
        string="Natureza do Rendimento",
        required=True,
    )
    ret_ir = fields.Boolean(
        string="Reter IR?",
    )
    ret_agreg = fields.Boolean(
        string="Reter de forma Agregada?",
    )
    ret_csll = fields.Boolean(
        string="Reter CSLL?",
    )
    ret_cofins = fields.Boolean(
        string="Reter COFINS?",
    )
    ret_pp = fields.Boolean(
        string="Reter Pis/Pasep?",
    )

    @api.depends('codigo', 'natureza_rendimento')
    def _compute_name(self):
        for record in self:
            record.name = '{} - {}'.format(
                record.codigo, record.natureza_rendimento)
