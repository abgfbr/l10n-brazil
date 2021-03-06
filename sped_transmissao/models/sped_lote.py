# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import base64
import tempfile
from datetime import datetime
import logging
import pysped
from openerp.tools import config
from openerp import api, fields, models
from openerp.exceptions import ValidationError, RedirectWarning
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

_logger = logging.getLogger(__name__)

TIPO_REGISTRO = {
    'S-1000': 1,
    'S-1005': 2,
    'S-1010': 3,
    'S-1020': 4,
    'S-1030': 5,
    'S-1035': 6,
    'S-1040': 7,
    'S-1050': 8,
    'S-1060': 9,
    'S-1070': 10,
    'S-1080': 11,
    'S-2190': 12,
    'S-2200': 13,
    'S-2205': 14,
    'S-2206': 15,
    'S-2210': 16,
    'S-2220': 17,
    'S-2230': 18,
    'S-2240': 19,
    'S-2241': 20,
    'S-2245': 21,
    'S-2250': 22,
    'S-2260': 23,
    'S-2298': 24,
    'S-2299': 25,
    'S-2300': 26,
    'S-2306': 27,
    'S-2399': 28,
    'S-2400': 29,
    'S-3000': 30,
    'S-1200': 31,
    'S-1202': 32,
    'S-1207': 33,
    'S-1210': 33,
    'S-1250': 35,
    'S-1260': 36,
    'S-1270': 37,
    'S-1280': 38,
    'S-1295': 39,
    'S-1300': 40,
    'S-1298': 41,
    'S-1299': 42,
}


class SpedLote(models.Model, ):
    _name = 'sped.lote'
    _inherit = []
    _description = 'Lotes de transmissões de registros SPED'
    _rec_name = 'codigo'
    _order = "ordem_registro ASC, data_hora_transmissao DESC, tipo, grupo, situacao"

    codigo = fields.Char(
        string='Código',
        default=lambda self: self.env['ir.sequence'].next_by_code('sped.lote'),
        readonly=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('efdreinf', 'EFD-Reinf'),
            ('esocial', 'e-Social'),
        ],
    )
    grupo = fields.Selection(
        string='Grupo',
        selection=[
            ('na', 'N/A'),
            ('1', 'Eventos de Tabela'),
            ('2', 'Eventos Não Periódicos'),
            ('3', 'Eventos Periódicos'),
            ('4', 'Fechamento'),
        ],
        default='na',
    )
    ordem_registro = fields.Integer(
        string='Ordem de envio do registro',
    )
    ambiente = fields.Selection(
        string='Ambiente',
        selection=[
            ('1', 'Produção'),
            ('2', 'Produção Restrita'),
            ('3', 'Homologação'),
        ],
    )
    transmissao_ids = fields.Many2many(
        string='Registros',
        comodel_name='sped.registro',
    )
    quantidade = fields.Integer(
        string='Registros',
        compute='compute_quantidade',
        store=True,
    )
    data_hora_transmissao = fields.Datetime(
        string='Data/Hora da Transmissão',
    )
    data_hora_retorno = fields.Datetime(
        string='Data/Hora do Retorno',
    )
    situacao = fields.Selection(
        string='Situação',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            # ('5', 'Precisa Retificar'),
        ],
        default='1',
    )

    # Dados de Envio
    envio_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML enviado',
        copy=False,
    )
    envio_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    cd_resposta = fields.Char(
        string='Código de Resposta',
    )
    desc_resposta = fields.Char(
        string='Reposta',
    )
    tempo_estimado = fields.Char(
        string='Tempo Estimado de Conclusão',
    )

    # Dados de Resposta
    retorno_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de retorno',
        copy=False,
    )
    retorno_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )
    dh_recepcao = fields.Char(
        string='Data/Hora da Recepção',
    )
    versao_aplicativo_recepcao = fields.Char(
        string='Versão Aplicativo de Recepção',
    )
    versao_aplicativo_processamento = fields.Char(
        string='Versão Aplicativo de Processamento',
    )
    protocolo = fields.Char(
        string='Protocolo',
    )
    ocorrencia_ids = fields.One2many(
        string='Ocorrências',
        comodel_name='sped.ocorrencia',
        inverse_name='lote_id',
    )
    ocorrencias = fields.Boolean(
        string='Tem ocorrencias?',
        compute='_compute_ocorrencias',
    )

    @api.depends('ocorrencia_ids')
    def _compute_ocorrencias(self):
        for lote in self:
            lote.ocorrencias = True if lote.ocorrencia_ids else False

    # Dados da Consulta
    consulta_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de consulta',
        copy=False,
    )
    consulta_xml = fields.Text(
        string='XML',
        compute='_compute_arquivo_xml',
    )

    @api.multi
    def unlink(self):
        for lote in self:
            if lote.situacao not in ['1', '3']:
                raise ValidationError("Não pode excluir um Lote transmitido!")
            if lote.situacao in ['3']:
                # Mudar o status dos registros deste lote para 'Pendente'
                for registro in lote.transmissao_ids:
                    registro.situacao = '1'
            super(SpedLote, lote).unlink()

    @api.depends('transmissao_ids')
    def compute_quantidade(self):
        for lote in self:
            lote.quantidade = len(lote.transmissao_ids)

    @api.depends('envio_xml_id', 'retorno_xml_id', 'consulta_xml')
    def _compute_arquivo_xml(self):
        for documento in self:
            dados = {
                'envio_xml': False,
                'retorno_xml': False,
                'consulta_xml': False,
            }

            if documento.envio_xml_id:
                dados['envio_xml'] = documento.envio_xml_id.conteudo_xml

            if documento.retorno_xml_id:
                dados['retorno_xml'] = documento.retorno_xml_id.conteudo_xml

            if documento.consulta_xml_id:
                dados['consulta_xml'] = documento.consulta_xml_id.conteudo_xml

            documento.update(dados)

    # Consulta o resultado do Lote
    @api.multi
    def consultar(self):
        self.ensure_one()

        # Gravar certificado em arquivo temporario
        arquivo = tempfile.NamedTemporaryFile()
        arquivo.seek(0)
        arquivo.write(
            base64.decodestring(self.company_id.nfe_a1_file)
        )
        arquivo.flush()

        # Cria o processador, dependendo do tipo do arquivo
        if self.tipo == 'efdreinf':
            processador = pysped.ProcessadorEFDReinf()

        elif self.tipo == 'esocial':
            processador = pysped.ProcessadorESocial()

        else:
            raise Exception("Não é um tipo que possa ser consultado !")

        # Popula o certificado no processador
        processador.caminho = self.mount_path()
        processador.certificado.arquivo = arquivo.name
        processador.certificado.senha = self.company_id.nfe_a1_password
        processador.ambiente = int(self.ambiente)

        # Executa a consulta
        if self.tipo == 'efdreinf':

            # Carrega os dados de consulta
            processador.tipoInscricaoContribuinte = '1'
            processador.numeroInscricaoContribuinte = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
            processador.numeroProtocoloFechamento = self.protocolo
            processo = processador.consultar_fechamento(ambiente=int(self.ambiente))

        else:

            # Consulta
            processador.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)
            processo = processador.consultar_lote(self.protocolo)

        # Guarda os dados de retorno do Lote
        self.cd_resposta = processo.resposta.cdResposta     # TODO Incluir no processador do REINF as mesmas
        self.desc_resposta = processo.resposta.descResposta # variáveis da resposta do eSocial para equalizar
        if self.tipo == 'esocial':
            self.dh_recepcao = processo.resposta.dhRecepcao   # o tratamento da resposta
            self.versao_aplicativo_recepcao = processo.resposta.versaoAplicativoRecepcao
            self.versao_aplicativo_processamento = processo.resposta.versaoAplicativoProcessamentoLote
            # self.protocolo = processo.resposta.protocoloEnvio  # Não acho correto poder mudar o protocoloEnvio aqui

        # Limpar ocorrências
        for ocorrencia in self.ocorrencia_ids:
            ocorrencia.unlink()

        # Popula as ocorrências do Lote
        if len(processo.resposta.ocorrencias) > 0:
            for ocorrencia in processo.resposta.ocorrencias:
                if self.tipo == 'esocial':
                    vals = {
                        'lote_id': self.id,
                        'tipo': ocorrencia.tipo.valor,
                        'local': ocorrencia.localizacao.valor,
                        'codigo': ocorrencia.codigo.valor,
                        'descricao': ocorrencia.descricao.valor,
                    }
                elif self.tipo == 'efdreinf':
                    vals = {
                        'lote_id': self.id,
                        'tipo': ocorrencia.tpOcorr.valor,
                        'local': ocorrencia.localErroAviso.valor,
                        'codigo': ocorrencia.codResp.valor,
                        'descricao': ocorrencia.dscResp.valor,
                    }
                self.ocorrencia_ids.create(vals)

        # Atualiza o XML de Consulta (retorno da consulta)
        if self.consulta_xml_id:
            consulta = self.consulta_xml_id
            consulta.consulta_xml_id = False
            consulta.unlink()
        consulta_xml = processo.resposta.xml
        consulta_xml_nome = self.codigo + '-consulta.xml'
        anexo_id = self._grava_anexo(consulta_xml_nome, consulta_xml)
        self.consulta_xml_id = anexo_id

        # Lote Aguardando Processamento (nada mais a fazer no momento)
        if processo.resposta.cdResposta == '101':
            return

        # O Lote foi rejeitado (nada mais a fazer)
        if int(processo.resposta.cdResposta) > 400:
            self.situacao = '3'
            return
        
        if self.tipo == 'esocial':
            eventos = processo.resposta.lista_eventos
            if processo.resposta.cdResposta == '201':
                self.situacao = '4'
            else:
                self.situacao = '2'
        elif self.tipo == 'efdreinf':
            eventos = [processo.resposta.evento]
            if processo.resposta.cdResposta == '0':
                self.situacao = '4'
            elif processo.resposta.cdResposta == '1':
                self.situacao = '3'
            elif processo.resposta.cdResposta == '2':
                self.situacao = '2'
            elif processo.resposta.cdResposta == '3':
                self.situacao = '1'

        # Processar os eventos
        for evento in eventos:

            # Localiza o evento pelo ID
            id = evento.Id.valor

            registro = False
            if self.tipo == 'esocial':
                registro = self.env['sped.registro'].search([('id_evento', '=', id)])
                if not registro:
                    raise ValidationError("ID %s não encontrado !" % id)
            elif self.tipo == 'efdreinf':
                registro = self.transmissao_ids[0]

            # Se o registro não foi encontrado, pula
            if not registro:
                continue

            # registro = self.env['sped.registro'].search([('id_evento', '=', id)])
            # if not registro:
            #     raise ValidationError("ID %s não encontrado !" % id)

            if self.tipo == 'esocial':
                codigo_retorno = evento.codigo_retorno
                descricao_retorno = evento.descricao_retorno
                ocorrencias = evento.lista_ocorrencias
            elif self.tipo == 'efdreinf':
                codigo_retorno = evento.ideRecRetorno.ideStatus.cdRetorno.valor
                descricao_retorno = evento.ideRecRetorno.ideStatus.descRetorno.valor
                ocorrencias = evento.ideRecRetorno.ideStatus.regOcorrs

            registro.cd_retorno = codigo_retorno
            registro.desc_retorno = descricao_retorno

            # Limpar ocorrências
            for ocorrencia in registro.ocorrencia_ids:
                ocorrencia.unlink()

            # Popula as ocorrências (se teve alguma)
            for ocorrencia in ocorrencias:
                if self.tipo == 'esocial':
                    vals = {
                        'transmissao_id': registro.id,
                        'tipo': ocorrencia['tipo'],
                        'codigo': ocorrencia['codigo'],
                        'descricao': ocorrencia['descricao'],
                        'local': ocorrencia['localizacao'],
                    }
                elif self.tipo == 'efdreinf':
                    vals = {
                        'transmissao_id': registro.id,
                        'tipo': ocorrencia.tpOcorr.valor,
                        'codigo': ocorrencia.codResp.valor,
                        'descricao': ocorrencia.dscResp.valor,
                        'local': ocorrencia.localErroAviso.valor,
                    }
                self.ocorrencia_ids.create(vals)

            # Atualiza o status do evento
            if self.tipo == 'esocial':
                if evento.codigo_retorno in ['201', '202']:
                    registro.recibo = evento.recibo
                    registro.hash = evento.hash
                    registro.situacao = '4'
                else:
                    registro.situacao = '3'
            elif self.tipo == 'efdreinf':
                if registro.cd_retorno == '0':
                    registro.situacao = '4'
                elif registro.cd_retorno == '1':
                    registro.situacao = '3'
                elif registro.cd_retorno == '2':
                    registro.situacao = '2'
                else:
                    registro.situacao = '1'

            # Atualiza o XML de Fechamento (retorno da consulta)
            if registro.consulta_xml_id:
                consulta = registro.consulta_xml_id
                registro.consulta_xml_id = False
                consulta.unlink()
            consulta_xml = evento.xml
            consulta_xml_nome = registro.id_evento + '-consulta.xml'
            anexo_id = registro._grava_anexo(consulta_xml_nome, consulta_xml)
            registro.consulta_xml_id = anexo_id

            # Se não houve erros no registro, rode o método retorno_sucesso() do registro intermediário
            if registro.situacao == '4':
                registro.retorno_sucesso(evento)

    # Transmite todos os registros contidos neste lote
    @api.multi
    def transmitir(self):
        self.ensure_one()

        # Se o lote já foi transmitido, não transmite de novo
        if self.situacao not in ['1', '3']:
            return True

        # Gravar certificado em arquivo temporario
        arquivo = tempfile.NamedTemporaryFile()
        arquivo.seek(0)
        arquivo.write(
            base64.decodestring(self.company_id.nfe_a1_file)
        )
        arquivo.flush()

        eventos = []
        sequencia = 1
        for registro in self.transmissao_ids:
            if registro.registro not in ['S-5001', 'S-5002', 'S-5011', 'S-5012']:
                evento, validacao = registro.calcula_xml(sequencia=sequencia)
                if not validacao:
                    eventos.append(evento)
                    sequencia += 1

        # Se não gerou nenhum XML, não precisa transmitir
        if not eventos:
            return False

        # Popula a data/hora da transmissão do lote
        data_hora_transmissao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.data_hora_transmissao = data_hora_transmissao

        # Popula o processador
        if self.tipo == 'efdreinf':
            processador = pysped.ProcessadorEFDReinf()
        else:
            processador = pysped.ProcessadorESocial()
        processador.salvar_arquivos = True
        processador.caminho = self.mount_path()
        processador.certificado.arquivo = arquivo.name
        processador.certificado.senha = self.company_id.nfe_a1_password
        processador.ambiente = int(self.ambiente)

        # Define a Inscrição do Processador
        processador.tpInsc = '1'
        processador.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)
        
        # Transmite
        if self.grupo != 'na':
            grupo = '3' if self.grupo == '4' else self.grupo
            processo = processador.enviar_lote(eventos, grupo)
        else:
            processo = processador.enviar_lote(eventos)

        # Guarda os XMLs de envio e retorno do lote
        envio_xml = processo.envio.xml
        envio_xml_nome = self.codigo + '-env.xml'
        retorno_xml = processo.resposta.xml
        retorno_xml_nome = self.codigo + '-ret.xml'

        # Grava anexos
        if envio_xml:
            if self.envio_xml_id:
                envio = self.envio_xml_id
                self.envio_xml_id = False
                envio.unlink()
            anexo_id = self._grava_anexo(envio_xml_nome, envio_xml)
            self.envio_xml_id = anexo_id
        if retorno_xml:
            if self.retorno_xml_id:
                retorno = self.retorno_xml_id
                self.retorno_xml_id = False
                retorno.unlink()
            anexo_id = self._grava_anexo(retorno_xml_nome, retorno_xml)
            self.retorno_xml_id = anexo_id

        # Limpar ocorrências do Lote
        for ocorrencia in self.ocorrencia_ids:
            ocorrencia.unlink()

        # Guarda os dados de retorno do Lote
        if self.tipo == 'efdreinf':   # Estes campos somente existem no retorno EFD/Reinf
            self.cd_resposta = processo.resposta.cdRetorno
            self.desc_resposta = processo.resposta.descRetorno
        elif self.tipo == 'esocial':  # Estes campos somente existem no retorno e-Social
            self.cd_resposta = processo.resposta.cdResposta
            self.desc_resposta = processo.resposta.descResposta
            self.dh_recepcao = processo.resposta.dhRecepcao
            self.versao_aplicativo_recepcao = processo.resposta.versaoAplicativoRecepcao
            self.protocolo = processo.resposta.protocoloEnvio

        # Se teve ocorrências do lote, armazená-las
        for ocorrencia in processo.resposta.ocorrencias:
            vals = {
                'lote_id': self.id,
                'tipo': ocorrencia.tipo.valor,
                'codigo': ocorrencia.codigo.valor,
                'descricao': ocorrencia.descricao.valor,
            }
            if self.tipo == 'efdreinf':
                vals['local'] = ocorrencia.localizacaoErroAviso.valor
            elif self.tipo == 'esocial':
                vals['local'] = ocorrencia.localizacao.valor

            self.ocorrencia_ids.create(vals)

        # Processa o status do retorno (valores de retorno são muito diferentes do eSocial e EFD/Reinf
        if self.tipo == 'efdreinf':

            # Popula o status do lote
            if self.cd_resposta == '0':

                # Se for o envio do fechamento, precisa marcar para consultar o retorno do lote ao invés de
                # interpretar que os registros foram enviados com sucesso ou não.
                fechamento = False
                for registro in self.transmissao_ids:
                    if registro.registro == 'R-2099':  # Fechamento
                        fechamento = True
                if fechamento:
                    self.situacao = '2'
                else:
                    self.situacao = '4'

            elif self.cd_resposta == '1':
                self.situacao = '3'
            elif self.cd_resposta == '2':
                self.situacao = '2'
            else:
                self.situacao = '1'

            # Popula o resultado da transmissão de cada evento (transmissão sincrona somente no EFD/Reinf)
            for evento in processo.resposta.eventos:

                # Localiza o registro original pelo Id
                id = evento.evtTotal.infoRecEv.idEv.valor

                registro = self.env['sped.registro'].search([('id_evento', '=', id)])
                if not registro:
                    raise ValidationError("ID %s não encontrado !" % id)

                # Popula o status, protocolo e recibo
                if registro.limpar_db:
                    registro.cd_retorno = False
                    registro.desc_retorno = False
                else:
                    registro.cd_retorno = evento.evtTotal.ideRecRetorno.ideStatus.cdRetorno.valor
                    registro.desc_retorno = evento.evtTotal.ideRecRetorno.ideStatus.descRetorno.valor
                    registro.recibo = evento.evtTotal.infoTotal.nrRecArqBase.valor
                    registro.protocolo = evento.evtTotal.infoRecEv.nrProtEntr.valor
                    # Grava o protocolo no Lote para consulta
                    self.protocolo = evento.evtTotal.infoRecEv.nrProtEntr.valor
                
                # Limpa as ocorrências do registro
                for ocorrencia in registro.ocorrencia_ids:
                    ocorrencia.unlink()

                # Popula as novas ocorrências do registro (se houver)
                for ocorrencia in evento.evtTotal.ideRecRetorno.ideStatus.regOcorrs:
                    vals = {
                        'transmissao_id': registro.id,
                        'tipo': ocorrencia.tpOcorr.valor,
                        'local': ocorrencia.localErroAviso.valor,
                        'codigo': ocorrencia.codResp.valor,
                        'descricao': ocorrencia.dscResp.valor,
                    }
                    registro.ocorrencia_ids.create(vals)

                # Popula o status do registro
                if registro.cd_retorno == '0':
                    registro.situacao = '4'
                elif registro.cd_retorno == '1':
                    registro.situacao = '3'
                elif registro.cd_retorno == '2':
                    registro.situacao = '2'
                else:
                    registro.situacao = '1'

                # Atualiza o XML de Retorno (retorno do evento síncrono)
                if registro.retorno_xml_id:
                    retorno = registro.retorno_xml_id
                    registro.retorno_xml_id = False
                    retorno.unlink()
                retorno_xml = evento.xml
                retorno_xml_nome = registro.id_evento + '-retorno.xml'
                anexo_id = self._grava_anexo(retorno_xml_nome, retorno_xml)
                registro.retorno_xml_id = anexo_id

        elif self.tipo == 'esocial':

            # Popula situação do lote
            if self.cd_resposta in ['201', '202']:
                self.situacao = '2'     # Transmitida

                # Popula a situação como Transmitida em todos os eventos relacionados
                for registro in self.transmissao_ids:
                    registro.situacao = '2'

            else:
                self.situacao = '3'     # Erros
                                        # Se teve erro no lote, ele não foi transmitido portanto os registros
                                        # continuam pendentes transmissão

        return True

    @api.multi
    def _grava_anexo(self, nome_arquivo='', conteudo='', model=None, res_id=None):
        self.ensure_one()

        if model is None:
            model = self._name

        busca = [
            ('res_model', '=', model),
            ('res_id', '=', res_id if res_id is not None else self.id),
            ('name', '=', nome_arquivo),
        ]
        anexo = self.env['ir.attachment'].search(busca)
        anexo.unlink()

        if type(conteudo) != bytes:
            conteudo = conteudo.encode('utf-8')

        dados = {
            'name': nome_arquivo,
            'datas_fname': nome_arquivo,
            'res_model': model,
            'res_id': res_id if res_id is not None else self.id,
            'datas': base64.b64encode(conteudo),
            # 'mimetype': tipo,
        }

        anexo = self.env['ir.attachment'].create(dados)

        return anexo

    @api.model
    def transmitir_lotes_preparados(self):

        # Identifica se já tem algum lote transmitido, nesse caso, não faça nada pois o e-Social "sugere" que
        # se transmita apenas 1 lote por vez (apesar que dever ser síncrono)
        lote_transmitido = self.env['sped.lote'].search([
            ('situacao', '=', 2),
        ], limit=1)
        if lote_transmitido:
            # msg = "Lote {} está aguardando processamento, não pode transmitir em paralelo".\
            #     format(lote_transmitido.codigo)
            # _logger.info(msg)
            return True

        # Localiza se tem algum lote do grupo 'na' para transmitir (esses devem ser transmitidos primeiro)
        lote_para_transmitir = self.env['sped.lote'].search([
            ('grupo', '=', 'na'),
            ('situacao', '=', '1'),
        ], limit=1, order='ordem_registro ASC')

        # Se não tem um lote do grupo NA então busca um dos grupos numéricos
        if not lote_para_transmitir:
            lote_para_transmitir = self.env['sped.lote'].search([
                ('situacao', '=', '1'),
            ], limit=1, order='ordem_registro ASC')

        # Transmite o lote identificado
        if lote_para_transmitir:
            lote_para_transmitir.transmitir()
            msg = "Lote {} transmitido".format(lote_para_transmitir.codigo)
            _logger.info(msg)
        # else:
        #     msg = "Nenhum Lote SPED para ser transmitido no momento."
        #     _logger.info(msg)

    @api.model
    def consultar_lotes_transmitidos(self):

        # Identifica todos os lotes já transmitidos que precisem ser consultados
        lotes = self.env['sped.lote'].search([
            ('situacao', '=', 2),
        ])

        # Executa a consulta
        for lote in lotes:
            lote.consultar()
            msg = "Lote {} Consultado - (Resposta: {}-{})".format(lote.codigo, lote.cd_resposta, lote.desc_resposta)
            _logger.info(msg)

        return True

    @api.multi
    def mount_path(self):
        db_name = self.company_id._cr.dbname
        # cnpj = limpa_formatacao(self.company_id.cnpj_cpf)
        filestore = config.filestore(db_name)
        # sped_path = '/'.join([filestore, 'PySPED', cnpj])
        sped_path = '/'.join([filestore, 'PySPED'])
        return sped_path
