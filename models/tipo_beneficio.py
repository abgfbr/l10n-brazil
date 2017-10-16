# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models, _


class TipoBeneficio(models.Model):
    _name = 'esocial.tipo_beneficio'
    _description = 'Tipos de Benefícios Previdenciários dos Regimes Próprios de Previdência'
    _order = 'codigo'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    codigo = fields.Integer(
        string='Codigo',
        required=True,
    )
    nome = fields.Char(
        string='Nome',
        required=True,
    )
    descricao = fields.Text(
        string='Descrição',
    )
    name = fields.Char(
        compute='_calcula_name',
        store=True,
    )

    @api.depends('codigo', 'nome')
    def _calcula_name(self):
        for tipo in self:
            tipo.name = str(tipo.codigo) + '-' + tipo.nome

