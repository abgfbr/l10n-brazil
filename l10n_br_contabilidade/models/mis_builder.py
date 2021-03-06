# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from num2words import num2words
from mako.template import Template

MONTHS = {
    '01': 'Janeiro',
    '02': 'Fevereiro',
    '03': 'Março',
    '04': 'Abril',
    '05': 'Maio',
    '06': 'Junho',
    '07': 'Julho',
    '08': 'Agosto',
    '09': 'Setembro',
    '10': 'Outubro',
    '11': 'Novembro',
    '12': 'Dezembro',
}


class MisReportInstance(models.Model):
    _inherit = 'mis.report.instance'
    _order = 'date DESC'

    administrator_id = fields.Many2one(
        string=u'Administrador responsável',
        comodel_name='res.partner',
        compute='_compute_responsible',
        readonly=False,
        store=True,
    )
    accountant_id = fields.Many2one(
        string=u'Contador responsável',
        comodel_name='res.partner',
        compute='_compute_responsible',
        readonly=False,
        store=True,
    )
    considerations = fields.Text(
        string=u'Considerações finais',
        compute='_compute_considerations',
        store=True,
    )

    @api.depends('report_id.considerations')
    def _compute_considerations(self):
        for record in self:
            if record.considerations or not record.report_id:
                continue
            record.considerations = record.report_id.considerations

    @api.depends('date', 'company_id', 'period_ids')
    def _compute_responsible(self):
        for record in self:
            if not record.period_ids or (record.accountant_id and
                                         record.administrator_id):
                continue

            date_from = min(record.period_ids.mapped('date_from'))
            date_to = max(record.period_ids.mapped('date_to'))
            fiscal_years = self.env['account.fiscalyear'].search([
                '|',
                '&', ('date_start', '>=', date_from),
                ('date_start', '<=', date_to),
                '&', ('date_stop', '>=', date_from),
                ('date_stop', '<=', date_to)
            ])
            accountants = fiscal_years.mapped('accountant_id')
            administrators = fiscal_years.mapped('administrator_id')
            if accountants:
                record.accountant_id = accountants[0]
            if administrators:
                record.administrator_id = administrators[0]

    @api.multi
    def compute(self):
        result = super(MisReportInstance, self).compute()
        res = result[0]
        if self.administrator_id and self.accountant_id:
            res['footer'] = [{
                'administrator': {
                    'signature':
                        '______________________________________________',
                    'name': self.administrator_id.name or '',
                    'label': 'Administrador - CPF: %s' %
                             (self.administrator_id.cnpj_cpf or '')},
                'accountant': {
                    'signature':
                        '______________________________________________',
                    'name': self.accountant_id.name,
                    'label': 'Contador - CPF: %s CRC: %s' % (
                        self.accountant_id.cnpj_cpf or '',
                        self.accountant_id.crc_number or '')},
            }]

        today = fields.Date.today()

        res['today'] = {
            'day': today[-2:],
            'month': MONTHS[today[5:-3]],
            'year': today[:4],
        }

        if not self.considerations:
            res['considerations'] = ''
            return [res]

        kpi = self.report_id.kpi_ids.filtered(
            lambda k: k.name == 'resultado_liquido_do_periodo'
        )
        row = next(d['cols'] and d['cols'][0] for d in res['content']
                   if d['kpi_name'] == kpi[0].description) if kpi else None

        if row and row.get('val') and self.considerations:
            val = float(row.get('val'))
            split_val = '{:,}'.format(val).split('.')
            liquid = split_val[0].replace(',', '.') + ',' + split_val[1]

            lang = 'pt_BR'

            in_full = num2words(int(split_val[0].replace(',', '')),lang=lang) + ' reais e ' + \
                num2words(int(split_val[1]), lang=lang) + ' centavos'

            template = Template(
                self.considerations.encode('utf-8'),
                input_encoding='utf-8',
                output_encoding='utf-8',
                strict_undefined=True
            )

            res['considerations'] = template.render(
                liquid={'val': val, 'f': liquid, 'in_full': in_full},
                mr=self.report_id, today=res['today']).decode('utf-8')

        return result
