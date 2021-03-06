# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from openerp.addons.sped_transmissao.models.sped_lote import TIPO_REGISTRO

# GRUPO_0 = [  # Eventos de Ativação
#     'S-1000',  # Informações do Empregador/Contribuinte/Órgão Público (e-Social),
# ]

GRUPO_1 = [  # Registros de Tabela
    'S-1005',  # Tabela de Estabelecimentos, Obras ou Unidades de Órgãos Públicos
    'S-1010',  # Tabela de Rubricas
    'S-1020',  # Tabela de Lotações Tributárias
    'S-1030',  # Tabela de Cargos/Empregos Públicos
    'S-1035',  # Tabela de Carreiras Públicas
    'S-1040',  # Tabela de Funções/Cargos em Comissão
    'S-1050',  # Tabela de Horários/Turnos de Trabalho
    'S-1060',  # Tabela de Ambientes de Trabalho
    'S-1070',  # Tabela de Processos Administrativos/Judiciais
    'S-1080',  # Tabela de Operadores Portuários
]   # 12 Registros

GRUPO_2 = [
    'S-2190',   # Admissão de Trabalhador - Registro Preliminar
    'S-2200',   # Cadastramento Inicial do Vínculo e Admissão/Ingresso de Trabalhador
    'S-2205',   # Alteração de Dados Cadastrais do Trabalhador
    'S-2206',   # Alteração de Contrato de Trabalho
    'S-2210',   # Comunicação de Acidente de Trabalho
    'S-2220',   # Monitoramento da Saúde do Trabalhador
    'S-2230',   # Afastamento Temporário
    'S-2240',   # Condições Ambientais do Trabalho - Fatores de Risco
    'S-2241',   # Insalubridade, Periculosidade e Aposentadoria Especial
    'S-2245',   # Treinamentos, Capacitações, Exercícios Simulados e Outras Anotações
    'S-2250',   # Aviso Prévio
    'S-2260',   # Convocação para Trabalho Intermitente
    'S-2298',   # Reintegração
    'S-2299',   # Desligamento
    'S-2300',   # Trabalhador Sem Vínculo de Emprego/Estatutário - Início
    'S-2306',   # Trabalhador Sem Vínculo de Emprego/Estatutário - Alteração Contratual
    'S-2399',   # Trabalhador Sem Vínculo de Emprego/Estatutário - Término
    'S-2400',   # Cadastro de Benefícios Previdenciários - RPPS
    'S-3000',   # Exclusão de Eventos
]   # 18 Registros

GRUPO_3 = [
    'S-1200',   # Remuneração de trabalhador vinculado ao Regime Geral de Prev. Social
    'S-1202',   # Remuneração de servidor vinculado a Regime Próprio de Previd. Social
    'S-1207',   # Benefícios previdenciários - RPPS
    'S-1210',   # Pagamentos de Rendimentos do Trabalho
    'S-1250',   # Aquisição de Produção Rural
    'S-1260',   # Comercialização da Produção Rural Pessoa Física
    'S-1270',   # Contratação de Trabalhadores Avulsos Não Portuários
    'S-1280',   # Informações Complementares aos Eventos Periódicos
    'S-1295',   # Solicitação de Totalização para Pagamento em Contingência
    'S-1300',   # Contribuição Sindical Patronal
]   # 102 Registros

GRUPO_4 = [
    'S-1298',   # Reabertura dos Eventos Periódicos
    'S-1299',   # Fechamento dos Eventos Periódicos
]   # 2 Registros
# Total 42 Registros


class SpedCriacaoWizard(models.TransientModel):
    _name = 'sped.criacao.wizard'
    # _description = 'Criar Lotes de Transmissão'

    lote_ids = fields.Many2many(
        string='Lotes de Transmissão',
        comodel_name='sped.lote.wizard',
        relation='cricao_lote_wizard_rel',
    )

    @api.model
    def default_get(self, fields):
        res = super(SpedCriacaoWizard, self).default_get(fields)

        # Obtém a lista de registros para transmitir pelo wizard
        registros_originais = self.env['sped.registro'].browse(self.env.context.get('active_ids'))

        # Limpa a tabela do wizard
        for wizard in self.env['sped.criacao.wizard'].search([]):
            for lote in wizard.lote_ids:
                lote.unlink()
            wizard.unlink()

        lotes = self.popular(ids=registros_originais)

        # Atualiza o campo res para criar o registro corretamente
        res['lote_ids'] = [(6, 0, lotes)]

        return res

    @api.multi
    def popular(self, ids=[]):

        # Elimina da lista registros já transmitidos e/ou
        # em outros lotes pendentes transmissão ou retorno
        registros = []
        for registro in ids:
            if registro.situacao not in ['1', '3']:
                continue
            ja_tem_lote = False

            for lote in registro.lote_ids:
                if lote.situacao != '4':
                    ja_tem_lote = True
                    continue
            if not ja_tem_lote:
                registros.append(registro)

        # if len(registros) == 0:
        #     raise ValidationError("Os registros selecionados não podem ser incluídos em um novo lote!")

        # Agrupa os registros em seus respectivos lotes
        lotes = []
        for registro in registros:

            # Verifica se o lote correto para este registro já existe
            grupo = self.get_valor_grupo(registro)

            # Verifica se este registro já está em algum lote pré-existente
            lote = self.env['sped.lote.wizard'].search([
                ('registro_ids', 'in', registro.id)
            ])
            if lote:
                if lote.id not in lotes:
                    lotes.append(lote.id)
            else:

                # Verifica se o lote já foi criado anteriormente
                domain = [
                    ('tipo', '=', registro.tipo),
                    ('ambiente', '=', registro.ambiente),
                    ('grupo', '=', grupo),
                    ('company_id', '=', registro.company_id.id),
                    ('cheio', '=', False),
                ]
                lote = self.env['sped.lote.wizard'].search(domain)

                for lote_registros in lote:
                    if lote_registros and lote_registros.registro_ids and \
                            lote_registros.registro_ids[0].registro == registro.registro:
                        lote = lote_registros
                        break
                    else:
                        lote = False

                # Cria o lote caso não exista
                if not lote:
                    vals = {
                        'tipo': registro.tipo,
                        'ambiente': registro.ambiente,
                        'grupo': grupo,
                        'company_id': registro.company_id.id,
                    }
                    if registro.tipo == 'esocial':
                        vals['ordem_registro'] = TIPO_REGISTRO[registro.registro]

                    lote = self.env['sped.lote.wizard'].create(vals)
                    lotes.append(lote.id)
                else:
                    if lote.id not in lotes:
                        lotes.append(lote.id)

            # Adiciona este registro no lote
            lote.registro_ids = [(4, registro.id)]

        return lotes

    def get_valor_grupo(self, registro):
        grupo = 'na'
        if registro.registro in GRUPO_1:
            grupo = '1'
        elif registro.registro in GRUPO_2:
            grupo = '2'
        elif registro.registro in GRUPO_3:
            grupo = '3'
        elif registro.registro in GRUPO_4:
            grupo = '4'
        return grupo

    @api.multi
    def criar_lotes(self):
        self.ensure_one()

        lotes = []

        for lote in self.lote_ids:
            vals = {
                'tipo': lote.tipo,
                'ambiente': lote.ambiente,
                'company_id': lote.company_id.id,
                'grupo': lote.grupo,
                'situacao': '1',
                # 'lote_ids': [(6, 0, lote.registro_ids.ids)]
            }
            if lote.tipo == 'esocial':
                vals['ordem_registro'] = lote.ordem_registro
            novo_lote = self.env['sped.lote'].create(vals)
            for registro in lote.registro_ids:
                registro.lote_ids = [(4, novo_lote.id)]
            lotes.append(novo_lote.id)

        return {
            'name': 'Lotes Criados',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'sped.lote',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain':  "[('id', 'in', %s)]" % lotes,
            'context': {},
        }


class SpedLoteWizard(models.TransientModel):
    _name = 'sped.lote.wizard'

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
            ('0' , 'Iniciais'),
            ('1' , 'Eventos de Tabela'),
            ('2' , 'Eventos Não Periódicos'),
            ('3' , 'Eventos Periódicos'),
            ('4' , 'Fechamento'),
        ],
        default='na',
    )
    ambiente = fields.Selection(
        string='Ambiente',
        selection=[
            ('1', 'Produção'),
            ('2', 'Produção Restrita'),
            ('3', 'Homologação'),
        ],
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    registro_ids = fields.Many2many(
        string='Registros',
        comodel_name='sped.registro',
        relation='criacao_registro_rel',
    )
    ordem_registro = fields.Integer(
        string='Ordem de envio do registro',
    )
    quantidade = fields.Integer(
        string='Quantidade',
        compute='compute_quantidade',
        store=True,
    )
    cheio = fields.Boolean(
        string='Está cheio?',
        compute='compute_quantidade',
        store=True,
    )

    @api.depends('registro_ids')
    def compute_quantidade(self):
        for lote in self:
            lote.quantidade = len(lote.registro_ids)
            cheio = (len(lote.registro_ids) == 50)
            if not cheio:
                for registro in lote.registro_ids:
                    if registro.registro in ['R-1000', 'S-1000']:
                        cheio = True
            lote.cheio = cheio
