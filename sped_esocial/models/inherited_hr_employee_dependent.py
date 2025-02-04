# -*- coding: utf-8 -*-
# Copyright 2025 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrEmployeeDependent(models.Model):
    _inherit = 'hr.employee.dependent'

    in_esocial = fields.Boolean(
        string='Incluído no e-Social',
        default=False,
    )

    @api.multi
    def set_cadastro_dependentes_esocial(self):
        for record in self:
            record.in_esocial = True
