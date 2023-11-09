# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import \
    SpedRegistroIntermediario
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor


class SpedEfdReinfEstab4020(models.Model, SpedRegistroIntermediario):
    _name = 'sped.efdreinf.estabelecimento.4020'
    _description = u'Prestadores de Eventos Periodicos EFD/Reinf R-4020'
    _rec_name = 'nome'
    _order = "nome"

    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        store=True,
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    efdreinf_id = fields.Many2one(
        string='EFD/Reinf',
        comodel_name='sped.efdreinf',
        ondelete="cascade",
    )
    estabelecimento_id = fields.Many2one(
        string='Estabelecimento',
        comodel_name='res.company',
    )
    prestador_id = fields.Many2one(
        string='Prestador',
        comodel_name='res.partner',
    )
    nfs_ids = fields.One2many(
        string='Notas Fiscais',
        comodel_name='sped.efdreinf.nfs.4020',
        inverse_name='estabelecimento_id',
    )
    vr_total_bruto = fields.Float(
        string='Valor Total Bruto',
        digits=[14, 2],
        compute='_get_totais_nfs',
    )
    vr_total_base_retencao = fields.Float(
        string='Base de Retenção',
        digits=[14, 2],
        compute='_get_totais_nfs',
    )
    vr_total_ret_princ = fields.Float(
        string='Total de Retenções',
        digits=[14, 2],
        compute='_get_totais_nfs',
    )
    sped_r4020 = fields.Boolean(
        string='Ativação EFD/Reinf',
        compute='_compute_sped_r4020',
    )
    sped_r4020_registro = fields.Many2one(
        string='Registro R-4020',
        comodel_name='sped.registro',
    )
    situacao_r4020 = fields.Selection(
        string='Situação R-4020',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Retificado'),
        ],
        compute='_compute_situacao',
        readonly=True,
    )
    sped_r4020_retificacao = fields.Many2one(
        string='Registro R-4020 (Retificação)',
        comodel_name='sped.registro',
    )

    @api.multi
    @api.depends('sped_r4020_registro')
    def _compute_situacao(self):
        situacao = '1'
        for record in self:
            if record.sped_r4020_registro:
                situacao = record.sped_r4020_registro.situacao

            if record.sped_r4020_registro.retificacao_ids:
                situacao = '6'
                for retificacao in record.sped_r4020_registro.retificacao_ids:
                    if retificacao.situacao in ['1', '3']:
                        situacao = retificacao.situacao
                        break

            record.situacao_r4020 = situacao

    @api.depends('estabelecimento_id', 'prestador_id')
    def _compute_nome(self):
        for prestador in self:
            nome = prestador.estabelecimento_id.name
            if prestador.prestador_id and prestador.prestador_id != prestador.estabelecimento_id:
                nome += '/' + prestador.prestador_id.name

            prestador.nome = nome

    @api.depends('sped_r4020_registro')
    def _compute_sped_r4020(self):
        for efdreinf in self:
            efdreinf.sped_r4020 = True if efdreinf.sped_r4020_registro else False

    @api.multi
    def _get_totais_nfs(self):
        for record in self:
            total_bruto = 0.0
            total_base_ret = 0.0
            total_ret = 0.0

            for nota in record.nfs_ids:
                total_bruto += nota.nfs_id.amount_untaxed
                total_base_ret += nota.nfs_id.amount_untaxed
                total_ret += nota.nfs_id.amount_wh - nota.nfs_id.inss_value_wh - nota.nfs_id.issqn_value_wh

            record.vr_total_bruto = total_bruto
            record.vr_total_base_retencao = total_base_ret
            record.vr_total_ret_princ = total_ret

    @api.multi
    def get_retencoes_nfs(self, nfs, R4020_retencoes):
        total_nfe = formata_valor(nfs.amount_total)
        if self.prestador_id.reinf_natureza_remuneracao_id.ret_ir:
            R4020_retencoes.vlrBaseIR.valor = formata_valor(nfs.irrf_base_wh)
            R4020_retencoes.vlrIR.valor = formata_valor(nfs.irrf_value_wh)
        if self.prestador_id.reinf_natureza_remuneracao_id.ret_agreg:
            R4020_retencoes.vlrBaseAgreg.valor = total_nfe
            R4020_retencoes.vlrAgreg.valor = formata_valor(
                nfs.amount_wh - nfs.inss_value_wh - nfs.irrf_value_wh)
        if not self.prestador_id.reinf_natureza_remuneracao_id.ret_agreg:
            if self.prestador_id.reinf_natureza_remuneracao_id.ret_csll:
                R4020_retencoes.vlrBaseCSLL.valor = total_nfe
                R4020_retencoes.vlrCSLL.valor = formata_valor(nfs.csll_value_wh)
            if self.prestador_id.reinf_natureza_remuneracao_id.ret_cofins:
                R4020_retencoes.vlrBaseCofins.valor = total_nfe
                R4020_retencoes.vlrCofins.valor = formata_valor(nfs.cofins_value_wh)
            if self.prestador_id.reinf_natureza_remuneracao_id.ret_pp:
                R4020_retencoes.vlrBasePP.valor = total_nfe
                R4020_retencoes.vlrPP.valor = formata_valor(nfs.pis_value_wh)

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):

        # Validação
        validacao = ""

        # Calcula o Período de Apuração no formato YYYY-MM
        periodo = self.efdreinf_id.periodo_id.code[3:7] + '-' + self.efdreinf_id.periodo_id.code[0:2]

        # Cria o registro
        R4020 = pysped.efdreinf.leiaute.R4020_2()

        # Popula ideEvento
        R4020.evento.ideEvento.tpAmb.valor = ambiente
        R4020.evento.ideEvento.indRetif.valor = '1'
        # Registro Original
        indRetif = '1'
        # Se for uma retificação
        if operacao == 'R':
            indRetif = '2'
            # Identifica o Recibo a ser retificado
            registro_para_retificar = self.sped_r4020_registro
            tem_retificacao = True
            while tem_retificacao:
                if registro_para_retificar.retificacao_ids and \
                        registro_para_retificar.retificacao_ids[
                            0].situacao not in ['1', '3']:
                    registro_para_retificar = \
                    registro_para_retificar.retificacao_ids[0]
                else:
                    tem_retificacao = False
            R4020.evento.ideEvento.nrRecibo.valor = registro_para_retificar.recibo
        R4020.evento.ideEvento.indRetif.valor = indRetif

        R4020.evento.ideEvento.procEmi.valor = '1'  # Processo de Emissão = Aplicativo do Contribuinte
        R4020.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0
        R4020.evento.ideEvento.perApur.valor = periodo

        # Popula ideContri (Dados do Contribuinte)
        R4020.evento.ideContri.tpInsc.valor = '1'
        if self.estabelecimento_id.eh_empresa_base:
            matriz = self.estabelecimento_id
        else:
            matriz = self.estabelecimento_id.matriz
        R4020.evento.ideContri.nrInsc.valor = limpa_formatacao(
            matriz.cnpj_cpf)[0:8]

        R4020.evento.ideEstab.tpInscEstab.valor = '1'
        R4020.evento.ideEstab.nrInscEstab.valor = limpa_formatacao(
            self.estabelecimento_id.cnpj_cpf)

        R4020.evento.ideEstab.ideBenef.cnpjBenef.valor = limpa_formatacao(
            self.prestador_id.cnpj_cpf)
        R4020.evento.ideEstab.ideBenef.isenImun.valor = 1

        R4020_idePgto = pysped.efdreinf.leiaute.R4020_IdePgto_2()
        R4020_idePgto.natRend.valor = \
            self.prestador_id.reinf_natureza_remuneracao_id.codigo

        for nfs in self.nfs_ids:
            R4020_infoPgto = pysped.efdreinf.leiaute.R4020_InfoPgto_2()
            R4020_infoPgto.dtFG.valor = nfs.nfs_id.data_pagamento
            R4020_infoPgto.vlrBruto.valor = formata_valor(nfs.vr_bruto)

            R4020_retencoes = pysped.efdreinf.leiaute.R4020_Retencoes_2()
            self.get_retencoes_nfs(nfs.nfs_id, R4020_retencoes)
            R4020_infoPgto.retencoes.append(R4020_retencoes)

            R4020_idePgto.infoPgto.append(R4020_infoPgto)

        R4020.evento.ideEstab.ideBenef.idePgto.append(R4020_idePgto)

        return R4020, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
