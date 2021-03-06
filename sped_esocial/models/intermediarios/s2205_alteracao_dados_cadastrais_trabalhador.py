# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


ESTADO_CIVIL = {
    'single': 1,
    'married': 2,
    'divorced': 3,
    'separated': 4,
    'widower': 5,
}


class SpedEmpregador(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.alteracao.funcionario"
    _rec_name = "name"
    _order = "company_id"

    name = fields.Char(
        string='name',
        compute='_compute_display_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    hr_employee_id = fields.Many2one(
        string='Funcionário',
        comodel_name='hr.employee',
        required=True,
    )
    sped_alteracao = fields.Many2one(
        string='Alteração',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Retificado'),
            ('7', 'Excluído'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
        store=True,
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_situacao_esocial',
    )

    @api.depends('hr_employee_id')
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2205 - Alteração Cadastral {}'.format(record.hr_employee_id.display_name or '')

    @api.depends('sped_alteracao.situacao')
    def compute_situacao_esocial(self):
        for s2205 in self:
            situacao_esocial = '1'
            ultima_atualizacao = False

            # Usa o status do registro de inclusão
            if s2205.sped_alteracao:
                situacao_esocial = s2205.sped_alteracao.situacao
                ultima_atualizacao = s2205.sped_alteracao.data_hora_origem

            # Popula na tabela
            s2205.situacao_esocial = situacao_esocial
            s2205.ultima_atualizacao = ultima_atualizacao

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def gerar_registro(self):
        self.ensure_one()

        # Criar o registro S-2205 de alteração, se for necessário
        values = {
            'tipo': 'esocial',
            'registro': 'S-2205',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtAltCadastral',
            'origem': ('hr.employee,%s' % self.hr_employee_id.id),
            'origem_intermediario': (
                    'sped.esocial.alteracao.funcionario,%s' % self.id),
        }
        if not self.sped_alteracao:
            sped_alteracao = self.env['sped.registro'].create(values)
            self.sped_alteracao = sped_alteracao

    @api.multi
    def popula_xml(self, ambiente='2', operacao='na'):
        """
        Função para popular o xml com os dados referente a alteração de
        dados cadastrais do funcionário
        """

        # Validação
        validacao = ""

        # Cria o registro
        S2205 = pysped.esocial.leiaute.S2205_2()
        empregado_id = self.hr_employee_id

        # Popula ideEvento
        S2205.tpInsc = '1'
        S2205.nrInsc = limpa_formatacao(
            empregado_id.company_id.cnpj_cpf
        )[0:8]
        S2205.evento.ideEvento.indRetif.valor = '1'
        if operacao == 'R':  # Retificação
            S2205.evento.ideEvento.indRetif.valor = '2'
            S2205.evento.ideEvento.nrRecibo.valor = self.sped_alteracao.recibo
        S2205.evento.ideEvento.tpAmb.valor = int(ambiente)
        S2205.evento.ideEvento.procEmi.valor = '1'
        S2205.evento.ideEvento.verProc.valor = '8.0'

        # Popula ideEmpregador (Dados do Empregador)
        S2205.evento.ideEmpregador.tpInsc.valor = '1'
        S2205.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            empregado_id.company_id.cnpj_cpf)[0:8]

        # Popula ideTrabalhador (Identificação do Trabalhador)
        S2205.evento.ideTrabalhador.cpfTrab.valor = limpa_formatacao(
            empregado_id.cpf
        )

        # Popula alteracao (Alteração de dados cadastrais do Trabalhador)
        S2205.evento.alteracao.dtAlteracao.valor = fields.Datetime.now()

        dados_trabalhador = S2205.evento.alteracao.dadosTrabalhador
        dados_trabalhador.nisTrab.valor = limpa_formatacao(
            empregado_id.pis_pasep
        )
        dados_trabalhador.nmTrab.valor = empregado_id.name
        if empregado_id.gender == 'male':
            dados_trabalhador.sexo.valor = 'M'
        else:
            dados_trabalhador.sexo.valor = 'F'
        dados_trabalhador.racaCor.valor = empregado_id.ethnicity.code
        if empregado_id.marital:
            dados_trabalhador.estCiv.valor = ESTADO_CIVIL[empregado_id.marital]
        dados_trabalhador.grauInstr.valor = \
            empregado_id.educational_attainment.code
        
        # Popula nascimento (Informações do nascimento)
        dados_trabalhador.nascimento.dtNascto.valor = empregado_id.birthday
        if empregado_id.naturalidade:
            dados_trabalhador.nascimento.codMunic.valor = \
                empregado_id.naturalidade.state_id.ibge_code + \
                empregado_id.naturalidade.ibge_code
            dados_trabalhador.nascimento.uf.valor = \
                empregado_id.naturalidade.state_id.code
        dados_trabalhador.nascimento.paisNascto.valor = \
            empregado_id.pais_nascto_id.codigo
        dados_trabalhador.nascimento.paisNac.valor = \
            empregado_id.pais_nac_id.codigo
        dados_trabalhador.nascimento.nmMae.valor = empregado_id.mother_name
        dados_trabalhador.nascimento.nmPai.valor = empregado_id.father_name

        # Popula documentos (Informações dos documentos pessoais)
        if empregado_id.ctps:
            ctps = pysped.esocial.leiaute.S2205_CTPS_2()
            ctps.nrCtps.valor = empregado_id.ctps
            ctps.serieCtps.valor = empregado_id.ctps_series
            ctps.ufCtps.valor = empregado_id.ctps_uf_id.code
            dados_trabalhador.documentos.CTPS.append(ctps)

        # Popula RIC (Registro de Identificação Civil)
        rg = pysped.esocial.leiaute.S2205_RG_2()
        rg.nrRg.valor = empregado_id.rg
        rg.orgaoEmissor.valor = empregado_id.organ_exp
        rg.dtExped.valor = empregado_id.rg_emission
        dados_trabalhador.documentos.RIC.append(rg)

        # Popula CNH (Carteira Nacional de Habilitação)
        if self.hr_employee_id.driver_license:
            CNH = pysped.esocial.leiaute.S2205_CNH_2()
            CNH.nrRegCnh.valor = self.hr_employee_id.driver_license
            if self.hr_employee_id.cnh_dt_exped:
                CNH.dtExped.valor = self.hr_employee_id.cnh_dt_exped
            CNH.ufCnh.valor = self.hr_employee_id.cnh_uf.code
            CNH.dtValid.valor = self.hr_employee_id.expiration_date
            if self.hr_employee_id.cnh_dt_pri_hab:
                CNH.dtPriHab.valor = self.hr_employee_id.cnh_dt_pri_hab
            CNH.categoriaCnh.valor = self.hr_employee_id.driver_categ
            dados_trabalhador.documentos.CNH.append(CNH)

        # Popula endereco (Informações do endereço do Trabalhador)
        endereco_brasil = dados_trabalhador.endereco.brasil
        endereco_brasil.tpLograd.valor = empregado_id.address_home_id.tp_lograd.codigo
        endereco_brasil.dscLograd.valor = empregado_id.address_home_id.street
        endereco_brasil.nrLograd.valor = empregado_id.address_home_id.number \
            if empregado_id.address_home_id.number else 'S/N'
        endereco_brasil.bairro.valor = empregado_id.address_home_id.district
        endereco_brasil.cep.valor = limpa_formatacao(
            empregado_id.address_home_id.zip)
        endereco_brasil.codMunic.valor = \
            empregado_id.address_home_id.state_id.ibge_code + \
            empregado_id.address_home_id.l10n_br_city_id.ibge_code
        endereco_brasil.uf.valor = empregado_id.address_home_id.state_id.code

        # Popula Dependentes (Informações dos dependentes)
        for dependente in empregado_id.dependent_ids:
            dependente_xml = pysped.esocial.leiaute.S2205_Dependente_2()

            dependente_xml.tpDep.valor = '03'
            # dependente_xml.tpDep.valor = dependente.dependent_type_id.code
            dependente_xml.nmDep.valor = dependente.name
            dependente_xml.dtNascto.valor = dependente.dependent_dob
            if dependente.cnpj_cpf: dependente_xml.cpfDep.valor = \
                limpa_formatacao(dependente.cnpj_cpf)
            if dependente.dependent_verification:
                dependente_xml.depIRRF.valor = 'S'
            else:
                dependente_xml.depIRRF.valor = 'N'
            dependente_xml.depSF.valor = 'N'
            dependente_xml.incTrab.valor = 'N'

            dados_trabalhador.dependente.append(dependente_xml)

        # Popula trabEstrangeiro se pais_nascto_id diferente de Brasil
        if empregado_id.pais_nascto_id != self.env.ref('sped_tabelas.tab06_105'):
            TrabEstrangeiro = pysped.esocial.leiaute.S2205_TrabEstrangeiro_2()
            TrabEstrangeiro.classTrabEstrang.valor = empregado_id.class_trab_estrang
            if empregado_id.dt_chegada:
                TrabEstrangeiro.dtChegada.valor = empregado_id.dt_chegada
            TrabEstrangeiro.casadoBr.valor = empregado_id.casado_br
            TrabEstrangeiro.filhosBr.valor = empregado_id.filhos_br
            dados_trabalhador.trabEstrangeiro.append(TrabEstrangeiro)

        return S2205, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        self.hr_employee_id.precisa_atualizar = False

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.hr_employee_id

    @api.multi
    def transmitir(self):
        self.ensure_one()

        if self.situacao_esocial in ['1', '3']:
            # Identifica qual registro precisa transmitir
            registro = False
            if self.sped_alteracao.situacao in ['1', '3']:
                registro = self.sped_alteracao

            # Com o registro identificado, é só rodar o método
            # transmitir_lote() do registro
            if registro:
                registro.transmitir_lote()

    @api.multi
    def consultar(self):
        self.ensure_one()

        if self.situacao_esocial in ['2']:
            # Identifica qual registro precisa consultar
            registro = False
            if self.sped_alteracao.situacao == '2':
                registro = self.sped_alteracao

            # Com o registro identificado, é só rodar o método consulta_lote() do registro
            if registro:
                registro.consulta_lote()
