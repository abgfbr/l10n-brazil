# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE
#   Wagner Pereira <wagner.pereira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models


class TipoLotacaoTributaria(models.Model):
    _name = 'esocial.tipo_lotacao_tributaria'
    _description = 'Tipos de Lotação Tributária'
    _order = 'codigo'
    _sql_constraints = [
        ('codigo',
         'unique(codigo)',
         'Este código já existe !'
         )
    ]

    codigo = fields.Char(
        size=2,
        string='Codigo',
        required=True,
    )
    descricao = fields.Char(
        string='Nome',
        required=True,
    )
    preenchimento_campo = fields.Char(
        string='Preenchimento do campo {nrInsc}',
        required=True,
    )
    name = fields.Char(
        compute='_compute_name',
        store=True,
    )

    @api.onchange('codigo')
    def _valida_codigo(self):
        for lotacao in self:
            if lotacao.codigo:
                if lotacao.codigo.isdigit():
                    lotacao.codigo = lotacao.codigo.zfill(2)
                else:
                    res = {'warning': {
                        'title': _('Código Incorreto!'),
                        'message': _('Campo Código somente aceita números!'
                                     ' - Corrija antes de salvar')
                    }}
                    lotacao.codigo = False
                    return res

    @api.depends('codigo', 'descricao', 'preenchimento_campo')
    def _compute_name(self):
        for lotacao in self:
            lotacao.name = lotacao.codigo + '-' + lotacao.descricao + '-' + lotacao.preenchimento_campo
