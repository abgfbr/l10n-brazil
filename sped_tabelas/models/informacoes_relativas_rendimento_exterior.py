# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# Copyright 2018 ABGF - Wagner Pereira <wagner.pereira@abgf.gov.br>
# Copyright 2024 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class InformacoesRelativasRendimentoExterior(models.Model):
    _name = 'sped.informacoes.relativas.exterior'
    _description = 'Informacoes Relativas Rendimento Exterior'
    _order = 'codigo'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    codigo = fields.Char(
        size=3,
        string='Código',
        required=True,
    )

    descricao = fields.Char(
        string='Descrição',
        required=True,
    )
