# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models

DIADASEMANA = [
            ('1', 'Segunda-Feira'),
            ('2', 'Terça-Feira'),
            ('3', 'Quarta-Feira'),
            ('4', 'Quinta-Feira'),
            ('5', 'Sexta-Feira'),
            ('6', 'Sábado'),
            ('7', 'Domingo'),
            ('8', 'Dia variável'),
        ]


class ResourceCalendarAttendance(models.Model):

    _inherit = 'resource.calendar.attendance'

    # Campos de controle S-1050
    sped_turno_id = fields.Many2one(
        string='SPED Turno de Trabalho',
        comodel_name='sped.hr.turnos.trabalho',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        related='sped_turno_id.situacao_esocial',
        readonly=True,
    )

    turno_id = fields.Many2one(
        string='Turno',
        comodel_name='hr.turnos.trabalho'
    )
    name = fields.Char(
        required=False,
    )
    hour_from = fields.Float(
        required=False,
    )
    hour_to = fields.Float(
        required=False,
    )
    dayofweek = fields.Selection(
        required=False,
    )
    diadasemana = fields.Selection(
        string='Dia da Semana',
        selection=DIADASEMANA,
        required=True,
    )

    @api.onchange('diadasemana')
    def onchange_diadasemana(self):
        self.ensure_one()
        self.name = dict(self._fields['diadasemana'].selection).get(self.diadasemana)