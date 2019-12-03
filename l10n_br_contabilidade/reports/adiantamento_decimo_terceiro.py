# -*- encoding: utf-8 -*-
# Copyright (C) 2017  KMEE
# Copyright (C) 2018  ABGF
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime

from openerp import api, _
from openerp.addons.report_py3o.py3o_parser import py3o_report_extender


TIPO_FOLHA = ['ferias', 'decimo_terceiro', 'rescisao']
RUBRICAS = {
    'ferias': ['ADIANTAMENTO_13', 'FGTS'],
    'decimo_terceiro': [
        'PRIMEIRA_PARCELA_13', 'FGTS', 'SALARIO_13', 'FGTS_F_13', 'INSS'],
    'rescisao': ['PROP13', 'FGTS_F_13', 'INSS_13'],
}


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


class Funcionario(object):
    def __init__(self, contract_id, nome, adiantamento_ferias,
                 fgts_adiantamento_ferias, adiantamento, fgts_adiantamento,
                 rescisao, fgts_rescisao, inss_rescisao, segunda_parcela,
                 fgts_segunda_parcela, inss_segunda_parcela):
        self.id = contract_id
        self.nome = nome
        self.adiantamento_ferias = adiantamento_ferias
        self.fgts_adiantamento_ferias = fgts_adiantamento_ferias
        self.adiantamento = adiantamento
        self.fgts_adiantamento = fgts_adiantamento
        self.rescisao = rescisao
        self.fgts_rescisao = fgts_rescisao
        self.inss_rescisao = inss_rescisao
        self.segunda_parcela = segunda_parcela
        self.fgts_segunda_parcela = fgts_segunda_parcela
        self.inss_segunda_parcela = inss_segunda_parcela


def get_holerites_adiantamento(
        cr, uid, pool, wizard, tipo_de_folha, rubrica, context):
    """
    Função responsável por buscar os holerites com adiantamento de 13º salário.

    :return: Dicionário com o id de contrato como chave e a holerite como valor.
    """
    busca_ferias = [
        ('tipo_de_folha', '=', tipo_de_folha),
        ('company_id', 'in', wizard.company_ids.ids),
        ('ano', '=', int(wizard.period_id.fiscalyear_id.name)),
        ('mes_do_ano', '<=', int(wizard.period_id.code[:2])),
        ('state', 'in', ['done', 'verify']),
        ('is_simulacao', '=', False),
    ]
    payslip_obj = pool['hr.payslip']
    holerites = {}
    holerites_ids = payslip_obj.search(cr, uid, busca_ferias, context=context)
    for holerite in payslip_obj.browse(cr, uid, holerites_ids, context=context):
        adiantamento = holerite.line_ids.filtered(
                    lambda r: r.code == rubrica and r.total > 0)
        if adiantamento:
            holerites[holerite.contract_id.id] = adiantamento.total

    return holerites


def get_funcionarios_adiantamento(contract_id, valores):
    funcionarios = []
    for contract in tuple(contract_id):
        proporcional_rescisao = valores['rescisao']['PROP13'].get(contract.id, 0) - (valores['ferias']['ADIANTAMENTO_13'].get(contract.id, 0) + valores['decimo_terceiro']['PRIMEIRA_PARCELA_13'].get(contract.id, 0))
        segunda_parcela = valores['decimo_terceiro']['SALARIO_13'].get(contract.id, 0) - (valores['ferias']['ADIANTAMENTO_13'].get(contract.id, 0) + valores['decimo_terceiro']['PRIMEIRA_PARCELA_13'].get(contract.id, 0))
        funcionarios.append(
            Funcionario(
                contract.id,
                contract.employee_id.name,
                valores['ferias']['ADIANTAMENTO_13'].get(contract.id, 0),
                valores['ferias']['FGTS'].get(contract.id, 0),
                valores['decimo_terceiro']['PRIMEIRA_PARCELA_13'].get(contract.id, 0),
                valores['decimo_terceiro']['FGTS'].get(contract.id, 0),
                proporcional_rescisao if proporcional_rescisao > 0 else 0,
                valores['rescisao']['FGTS_F_13'].get(contract.id, 0),
                valores['rescisao']['INSS_13'].get(contract.id, 0),
                segunda_parcela if segunda_parcela > 0 else 0,
                valores['decimo_terceiro']['FGTS_F_13'].get(contract.id, 0),
                valores['decimo_terceiro']['INSS'].get(contract.id, 0),
            )
        )

    return funcionarios


def get_total_valores(funcionarios):
    total_adiantamento_ferias = 0
    total_fgts_adiantamento_ferias = 0
    total_adiantamento = 0
    total_fgts_adiantamento = 0
    total_recisao_decimo_terceiro = 0
    total_fgts_rescisao = 0
    total_inss_rescisao = 0
    total_segunda_parcela = 0
    total_fgts_segunda_parcela = 0
    total_inss_segunda_parcela = 0

    for funcionario in funcionarios:
        total_adiantamento_ferias += funcionario.adiantamento_ferias
        total_fgts_adiantamento_ferias += funcionario.fgts_adiantamento_ferias
        total_adiantamento += funcionario.adiantamento
        total_fgts_adiantamento += funcionario.fgts_adiantamento
        total_recisao_decimo_terceiro += funcionario.rescisao
        total_fgts_rescisao += funcionario.fgts_rescisao
        total_inss_rescisao += funcionario.inss_rescisao
        total_segunda_parcela += funcionario.segunda_parcela
        total_fgts_segunda_parcela += funcionario.fgts_segunda_parcela
        total_inss_segunda_parcela += funcionario.inss_segunda_parcela

    return total_adiantamento_ferias, total_fgts_adiantamento_ferias, \
        total_adiantamento, total_fgts_adiantamento, \
        total_recisao_decimo_terceiro, total_fgts_rescisao, \
        total_inss_rescisao, total_segunda_parcela, \
        total_fgts_segunda_parcela, total_inss_segunda_parcela


def formatar_valores(funcionarios):
    for funcionario in funcionarios:
        funcionario.adiantamento_ferias = format_money_mask(funcionario.adiantamento_ferias)
        funcionario.fgts_adiantamento_ferias = format_money_mask(funcionario.fgts_adiantamento_ferias)
        funcionario.adiantamento = format_money_mask(funcionario.adiantamento)
        funcionario.fgts_adiantamento = format_money_mask(funcionario.fgts_adiantamento)
        funcionario.rescisao = format_money_mask(funcionario.rescisao)
        funcionario.fgts_rescisao = format_money_mask(funcionario.fgts_rescisao)
        funcionario.inss_rescisao = format_money_mask(funcionario.inss_rescisao)
        funcionario.segunda_parcela = format_money_mask(funcionario.segunda_parcela)
        funcionario.fgts_segunda_parcela = format_money_mask(funcionario.fgts_segunda_parcela)
        funcionario.inss_segunda_parcela = format_money_mask(funcionario.inss_segunda_parcela)

    return funcionarios


@api.model
@py3o_report_extender(
    "l10n_br_contabilidade.report_adiantamento_decimo_terceiro_py3o_report")
def adiantamento_report(pool, cr, uid, local_context, context):
    """
    :return:
    """
    data = {}

    proxy = pool['adiantamento.decimo.terceiro.wizard']
    wizard = proxy.browse(cr, uid, context['active_id'])

    #
    # GET Holerites
    #
    valores = {}
    for tipo_folha in TIPO_FOLHA:
        rubricas = {}

        for rubrica in RUBRICAS[tipo_folha]:
            rubricas[rubrica] = get_holerites_adiantamento(
                cr, uid, pool, wizard, tipo_folha, rubrica, context)

        valores[tipo_folha] = rubricas

    data['funcionarios'] = get_funcionarios_adiantamento(
        wizard.contract_id, valores
    )

    total_adiantamento_ferias, total_fgts_adiantamento_ferias, \
        total_adiantamento, total_fgts_adiantamento, \
        total_recisao_decimo_terceiro, total_fgts_rescisao, \
        total_inss_rescisao, total_segunda_parcela, total_fgts_parcela, \
        total_inss_parcela = get_total_valores(data['funcionarios'])

    data['funcionarios'] = formatar_valores(data['funcionarios'])

    data['total_adiantamento_ferias'] = format_money_mask(total_adiantamento_ferias)
    data['total_fgts_adiantamento_ferias'] = format_money_mask(total_fgts_adiantamento_ferias)
    data['total_adiantamento'] = format_money_mask(total_adiantamento)
    data['total_fgts_adiantamento'] = format_money_mask(total_fgts_adiantamento)
    data['total_recisao_decimo_terceiro'] = format_money_mask(total_recisao_decimo_terceiro)
    data['total_fgts_rescisao'] = format_money_mask(total_fgts_rescisao)
    data['total_inss_rescisao'] = format_money_mask(total_inss_rescisao)
    data['total_segunda_parcela'] = format_money_mask(total_segunda_parcela)
    data['total_fgts_parcela'] = format_money_mask(total_fgts_parcela)
    data['total_inss_parcela'] = format_money_mask(total_inss_parcela)

    data['competencia'] = wizard.period_id.code

    # Rotina para formatar valores e data
    local_context.update(data)
