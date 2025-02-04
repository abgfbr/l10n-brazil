# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class SpedRegistro(models.Model):
    _inherit = 'sped.lote'

    @api.multi
    def consultar(self):
        res = super(SpedRegistro, self).consultar()

        if self.tipo == 'esocial':
            if self.situacao == '4':
                for evento in self.transmissao_ids:
                    if evento.situacao == '4':
                        if evento.registro in ['S-2200', 'S-1210']:
                            evento.employee_id.set_cadastro_dependentes_esocial()
