# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao


class SpedReinfContribuinteAbertura4000(models.Model):
    _name = "sped.efdreinf.abertura.eventos.4000"
    _rec_name = "nome"
    _order = "company_id"

    nome = fields.Char(
        string='Nome',
        compute='_compute_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    reinf_competencia_id = fields.Many2one(
        string='Competência do Reinf',
        comodel_name='sped.efdreinf',
        required=True,
    )
    situacao = fields.Selection(
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao',
    )
    # Registro R-4099
    sped_r4099_registro = fields.Many2one(
        string='Registro R-4099',
        comodel_name='sped.registro',
    )
    sped_r4099_registro_ids = fields.Many2many(
        string='Registros Anteriores',
        comodel_name='sped.registro',
    )

    @api.depends('company_id')
    def _compute_name(self):
        for registro in self:
            nome = 'Contribuinte'
            if registro.company_id:
                nome += ' ('
                nome += registro.company_id.display_name or ''
                nome += ') + R-4099 Abertura'
            registro.nome = nome

    @api.depends('sped_r4099_registro')
    def compute_situacao(self):
        for contribuinte in self:
            # Popula na tabela
            contribuinte.situacao = contribuinte.sped_r4099_registro.situacao

    @api.multi
    def criar_registro(self):
        values = {'tipo': 'efdreinf', 'registro': 'R-4099',
                  'ambiente': self.company_id.tpAmb,
                  'company_id': self.company_id.id, 'evento': 'evtFech4000',
                  'origem': ('sped.efdreinf,%s' % self.reinf_competencia_id.id),
                  'origem_intermediario': (
                          'sped.efdreinf.abertura.eventos.4000,%s' % self.id
                  ), 'operacao': 'I'}

        # Criar o registro R-4099 de inclusão, se for necessário
        sped_inclusao = self.env['sped.registro'].create(values)
        if not self.sped_r4099_registro:
            self.sped_r4099_registro = sped_inclusao
        else:
            self.sped_r4099_registro_ids = self.sped_r4099_registro
            self.sped_r4099_registro = sped_inclusao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # Calcula o Período de Apuração no formato YYYY-MM
        periodo = self.periodo_id.code[3:7] + '-' + self.periodo_id.code[0:2]

        # Cria o registro
        R4099 = pysped.efdreinf.leiaute.R4099_2()

        # Popula ideEvento
        R4099.evento.ideEvento.perApur.valor = periodo
        R4099.evento.ideEvento.tpAmb.valor = ambiente
        # Processo de Emissão = Aplicativo do Contribuinte
        R4099.evento.ideEvento.procEmi.valor = '1'
        R4099.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideContri (Dados do Contribuinte)
        R4099.evento.ideContri.tpInsc.valor = '1'
        R4099.evento.ideContri.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula ideRespInf
        R4099.evento.ideRespInf.nmResp.valor = self.company_id.nmctt
        R4099.evento.ideRespInf.cpfResp.valor = self.company_id.cpfctt
        if self.company_id.cttfonefixo:
            R4099.evento.ideRespInf.telefone.valor = self.company_id.cttfonefixo
        if self.company_id.cttemail:
            R4099.evento.ideRespInf.email.valor = self.company_id.cttemail

        R4099.evento.infoFech.fechRet.valor = '1'

        return R4099, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()