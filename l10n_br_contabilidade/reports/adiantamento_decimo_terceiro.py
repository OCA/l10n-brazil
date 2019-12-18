# -*- encoding: utf-8 -*-
# Copyright (C) 2019  ABGF
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api
from openerp.addons.report_py3o.py3o_parser import py3o_report_extender

TIPO_FOLHA = ['normal', 'decimo_terceiro', 'rescisao']

RUBRICAS = {
    'normal': ['ADIANTAMENTO_13_FERIAS', 'FGTS_F_13'],

    'decimo_terceiro': [
        'PRIMEIRA_PARCELA_13', 'MEDIA_SALARIO_SUBSTI_ADIANT_13', 'DIF_MEDIA_SALARIO_SUBSTI_ADIANT_13',
        'FGTS',
        'DESCONTO_ADIANTAMENTO_13',
        'DESCONTO_MEDIA_SALARIO_SUBSTI_ADIANT_13',
        'DESCONTO_DIF_MEDIA_SALARIO_SUBSTI_ADIANT_13',
    ],

    'rescisao': ['DESCONTO_ADIANTAMENTO_13','FGTS_F_13'],
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
                 rescisao, fgts_rescisao, segunda_parcela, fgts_segunda_parcela):
        self.id = contract_id
        self.nome = nome
        self.adiantamento_ferias = adiantamento_ferias
        self.fgts_adiantamento_ferias = fgts_adiantamento_ferias
        self.adiantamento = adiantamento
        self.fgts_adiantamento = fgts_adiantamento
        self.rescisao = rescisao
        self.fgts_rescisao = fgts_rescisao
        self.segunda_parcela = segunda_parcela
        self.fgts_segunda_parcela = fgts_segunda_parcela

        self.valido = any([
            adiantamento_ferias > 0,
            fgts_adiantamento_ferias > 0,
            adiantamento > 0,
            fgts_adiantamento > 0,
            rescisao > 0,
            fgts_rescisao > 0,
            segunda_parcela > 0,
            fgts_segunda_parcela > 0,
        ])


def get_holerites_adiantamento(
        cr, uid, pool, wizard, tipo_de_folha, rubrica, context):
    """
    Função responsável por buscar os holerites com adiantamento de 13º salário.

    :return: Dicionário com o id de contrato como chave e a holerite como valor.
    """
    busca_ferias = [
        ('tipo_de_folha', '=', tipo_de_folha),
        ('company_id', 'in', wizard.company_ids.ids),
        ('date_from', '<=', wizard.end_period_id.date_stop),
        ('date_from', '>=', wizard.start_period_id.date_start),
        ('state', 'in', ['done', 'verify']),
        ('is_simulacao', '=', False),
    ]

    if 'FGTS' in rubrica:
        busca_ferias.append(('contract_id.gerar_sefip', '=', True))

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

        primeira_parcela = \
            valores['decimo_terceiro']['PRIMEIRA_PARCELA_13'].get(contract.id, 0) + \
            valores['decimo_terceiro']['MEDIA_SALARIO_SUBSTI_ADIANT_13'].get(contract.id, 0) + \
            valores['decimo_terceiro']['DIF_MEDIA_SALARIO_SUBSTI_ADIANT_13'].get(contract.id, 0)

        if primeira_parcela and contract.gerar_sefip:
            fgts_primeira_parcela = primeira_parcela * 8 / 100
        else:
            fgts_primeira_parcela = 0

        segunda_parcela = \
            valores['decimo_terceiro'].get('DESCONTO_ADIANTAMENTO_13', {}).get(contract.id, 0) + \
            valores['decimo_terceiro'].get('DESCONTO_MEDIA_SALARIO_SUBSTI_ADIANT_13', {}).get(contract.id, 0) + \
            valores['decimo_terceiro'].get('DESCONTO_DIF_MEDIA_SALARIO_SUBSTI_ADIANT_13', {}).get(contract.id, 0)

        if segunda_parcela and contract.gerar_sefip:
            fgts_segunda_parcela = segunda_parcela * 8 / 100
        else:
            fgts_segunda_parcela = 0

        proporcional_rescisao = valores['rescisao']['DESCONTO_ADIANTAMENTO_13'].get(contract.id, 0)

        # Buscar valor do adiantamento na rescisao
        if proporcional_rescisao and contract.gerar_sefip:
            fgts_adiantamento = proporcional_rescisao * 8 / 100
        else:
            fgts_adiantamento = 0

        # Pagamento de 13 eh feito em novembro, adiantando o ultimo avo de DEZ
        # Para o caso do funcionario que foi rescindido depois do
        # pagamento do 13º e nao tinha direito a todos os avos (nao completou
        # o avo de dezembro). Na rescisao devera descontar o avo adiantado no
        # holerite do 13, e pagar o proporcional correto.
        valor_adiantado = \
            primeira_parcela + \
            valores['normal']['ADIANTAMENTO_13_FERIAS'].get(contract.id, 0)
        if proporcional_rescisao and not valor_adiantado:
            primeira_parcela = proporcional_rescisao
            fgts_primeira_parcela = fgts_adiantamento

        funcionario_obj = Funcionario(
            contract.id,
            contract.employee_id.name,
            valores['normal']['ADIANTAMENTO_13_FERIAS'].get(contract.id, 0),
            valores['normal']['FGTS_F_13'].get(contract.id, 0),
            primeira_parcela,
            fgts_primeira_parcela,
            proporcional_rescisao,
            fgts_adiantamento,
            segunda_parcela,
            fgts_segunda_parcela,
        )

        if funcionario_obj.valido:
            funcionarios.append(funcionario_obj)

    return funcionarios


def get_total_valores(funcionarios):
    total_adiantamento_ferias = 0
    total_fgts_adiantamento_ferias = 0
    total_adiantamento = 0
    total_fgts_adiantamento = 0
    total_recisao_decimo_terceiro = 0
    total_fgts_rescisao = 0
    total_segunda_parcela = 0
    total_fgts_segunda_parcela = 0

    for funcionario in funcionarios:
        total_adiantamento_ferias += funcionario.adiantamento_ferias
        total_fgts_adiantamento_ferias += funcionario.fgts_adiantamento_ferias
        total_adiantamento += funcionario.adiantamento
        total_fgts_adiantamento += funcionario.fgts_adiantamento
        total_recisao_decimo_terceiro += funcionario.rescisao
        total_fgts_rescisao += funcionario.fgts_rescisao
        total_segunda_parcela += funcionario.segunda_parcela
        total_fgts_segunda_parcela += funcionario.fgts_segunda_parcela

    return total_adiantamento_ferias, total_fgts_adiantamento_ferias, \
        total_adiantamento, total_fgts_adiantamento, \
        total_recisao_decimo_terceiro, total_fgts_rescisao, \
        total_segunda_parcela, \
        total_fgts_segunda_parcela

def formatar_valores(funcionarios):
    for funcionario in funcionarios:
        funcionario.adiantamento_ferias = format_money_mask(funcionario.adiantamento_ferias)
        funcionario.fgts_adiantamento_ferias = format_money_mask(funcionario.fgts_adiantamento_ferias)
        funcionario.adiantamento = format_money_mask(funcionario.adiantamento)
        funcionario.fgts_adiantamento = format_money_mask(funcionario.fgts_adiantamento)
        funcionario.rescisao = format_money_mask(funcionario.rescisao)
        funcionario.fgts_rescisao = format_money_mask(funcionario.fgts_rescisao)
        funcionario.segunda_parcela = format_money_mask(funcionario.segunda_parcela)
        funcionario.fgts_segunda_parcela = format_money_mask(funcionario.fgts_segunda_parcela)

    return funcionarios


@api.model
@py3o_report_extender(
    "l10n_br_contabilidade.report_adiantamento_decimo_terceiro_py3o_report")
def adiantamento_report(pool, cr, uid, local_context, context):
    """
    :return:
    """
    data = {}

    data['footer'] = \
        u'Telefone: 61-3246-6200 | E-mail: gecon@abgf.gov.br | ' \
        u'Site: http://www.abgf.gov.br'

    proxy = pool['res.company']
    company_id = proxy.browse(cr, uid, 1)

    company_logo = company_id.logo
    company_nfe_logo = company_id.nfe_logo

    data['company_id'] = company_id
    data['company_logo'] = \
        company_nfe_logo if company_nfe_logo else company_logo
    data['company_logo2'] = \
        company_nfe_logo if company_nfe_logo else company_logo

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
        total_segunda_parcela, total_fgts_parcela = get_total_valores(data['funcionarios'])

    data['funcionarios'] = formatar_valores(data['funcionarios'])
    data['competencia'] = '{} - {}'.format(
        wizard.start_period_id.code, wizard.end_period_id.code
    )

    data['total_adiantamento_ferias'] = format_money_mask(total_adiantamento_ferias)
    data['total_fgts_adiantamento_ferias'] = format_money_mask(total_fgts_adiantamento_ferias)

    data['total_adiantamento'] = format_money_mask(total_adiantamento)
    data['total_fgts_adiantamento'] = format_money_mask(total_fgts_adiantamento)

    data['total_recisao_decimo_terceiro'] = format_money_mask(total_recisao_decimo_terceiro)
    data['total_fgts_rescisao'] = format_money_mask(total_fgts_rescisao)

    data['total_segunda_parcela'] = format_money_mask(total_segunda_parcela)
    data['total_fgts_parcela'] = format_money_mask(total_fgts_parcela)

    data['resultado_adiantamento'] = format_money_mask(
        total_adiantamento_ferias +
        total_adiantamento -
        total_recisao_decimo_terceiro -
        total_segunda_parcela
    )

    data['resultado_fgts'] = format_money_mask(
        total_fgts_adiantamento_ferias +
        total_fgts_adiantamento -
        total_fgts_rescisao -
        total_fgts_parcela
    )

    # Rotina para formatar valores e data
    local_context.update(data)
