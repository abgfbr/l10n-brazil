# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - Hendrix Costa <hendrix.costa@abgf.giv.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from openerp import api
from openerp.addons.report_py3o.py3o_parser import py3o_report_extender


class LinhaTotalizador(object):
    def __init__(self):
        self.nome = ''
        self.base = ''
        self.desconto = ''


def format_money_mask(value):
    """
    Function to transform float values to pt_BR currency mask
    :param value: float value
    :return: value with brazilian money format
    """
    import locale
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
    value_formated = locale.currency(value, grouping=True)

    return value_formated[3:]

def get_registro_sucesso(registro):
    """
    :param registro:
    :return:
    """
    if registro.retificacao_ids:
        registro = get_registro_sucesso(registro.retificacao_ids[0])
    return registro

@api.model
@py3o_report_extender('sped_esocial.report_py3o_totalizador_periodo')
def totalizador_periodo(pool, cr, uid, localcontext, context):
    """

    """
    self = localcontext['objects']

    # Logo
    company_logo = self.env.user.company_id.logo
    company_nfe_logo = self.env.user.company_id.nfe_logo
    localcontext['company_logo'] = \
        company_nfe_logo if company_nfe_logo else company_logo
    localcontext['company_logo2'] = \
        company_nfe_logo if company_nfe_logo else company_logo

    # Variaveis de Informações
    data_atual = datetime.now()
    dia_atual = \
        str(data_atual.day) + "/" + str(data_atual.month) + "/" + \
        str(data_atual.year)

    contribuicao_mensal = []
    contribuicao_rescisao = []

    total_base = 0
    total_desconto = 0

    for remuneracao_id in self.remuneracao_ids:

        linha = LinhaTotalizador()

        # Pegar ultimo registro de sucesso
        registro_sucesso = get_registro_sucesso(remuneracao_id.sped_registro)
        
        linha.nome = remuneracao_id.contract_ids[0].display_name

        base = sum(registro_sucesso.origem.s5001_id.ideestablot_ids.filtered(
            lambda x: x.tp_valor == '11').mapped('valor')) or 0.00
        linha.base = format_money_mask(base)
        total_base += base

        desconto = sum(registro_sucesso.origem.s5001_id.ideestablot_ids.filtered(
            lambda x: x.tp_valor == '21').mapped('valor')) or 0.00
        linha.desconto = format_money_mask(desconto)
        total_desconto += desconto

        contribuicao_mensal.append(linha)

    for rescisao_id in self.desligamento_ids:

        registro_sucesso = get_registro_sucesso(
            rescisao_id.sped_s2299_registro_inclusao)

        for indicador_13 in ['0','1']:

            linha = LinhaTotalizador()

            linha.nome = rescisao_id.sped_hr_rescisao_id.contract_id.display_name

            base = registro_sucesso.sped_s5001.ideestablot_ids.filtered(
                lambda x: x.tp_valor == '11' and x.ind13 == indicador_13).valor or 0.00
            linha.base = format_money_mask(base)
            total_base += base

            desconto = registro_sucesso.sped_s5001.ideestablot_ids.filtered(
                lambda x: x.tp_valor == '21' and x.ind13 == indicador_13).valor or 0.00
            linha.desconto = format_money_mask(desconto)
            total_desconto += desconto

            contribuicao_rescisao.append(linha)

    data = {
        'object': self,
        'data_atual': data_atual,
        'contribuicao_mensal': contribuicao_mensal,
        'contribuicao_rescisao': contribuicao_rescisao,
        'total_base': format_money_mask(total_base),
        'total_desconto': format_money_mask(total_desconto),
    }
    localcontext.update(data)
