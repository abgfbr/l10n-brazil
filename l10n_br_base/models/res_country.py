# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class ResCountry(models.Model):
    _inherit = 'res.country'

    bc_code = fields.Char('Codigo BC', size=5)
    ibge_code = fields.Char('Codigo IBGE', size=5)
    siscomex_code = fields.Char('Codigo Siscomex', size=4)


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    ibge_code = fields.Char('Codigo IBGE', size=2)

    @api.model
    def get_states_ids(self, id_country):
        state_ids = self.search([('country_id.id', '=', id_country)])
        dict = {}
        for id in state_ids._ids:
            dict[id] = self.browse(id).name
        return dict