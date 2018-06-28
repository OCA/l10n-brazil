# -*- encoding: utf-8 -*-
# Copyright (C) 2017 - TODAY Albert De La Fuente - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime

from openerp import api
from openerp.addons.report_py3o.py3o_parser import py3o_report_extender
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import TIPO_DE_FOLHA

class inss_empresa_obj(object):
    def __init__(self, valores_inss_empresa):
        self.base = valores_inss_empresa['base']
        self.inss_empresa = valores_inss_empresa['inss_empresa']
        self.rat_fap = valores_inss_empresa['rat_fap']
        self.terceiros = valores_inss_empresa['terceiros']
        self.total = valores_inss_empresa['total']


class rubrica_obj(object):
    def __init__(self, rubrica):
        self.code = rubrica['code']
        self.name = rubrica['name']
        self.quantity = rubrica['quantity']
        self.sum = rubrica['sum']


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


def process_data_format(data):
    for line in data:
        if type(data[line]) is float:
            data[line] = format_money_mask(data[line])
            continue
        if type(data[line]) is inss_empresa_obj:
            data[line].base = format_money_mask(data[line].base)
            data[line].inss_empresa = format_money_mask(
                data[line].inss_empresa)
            data[line].rat_fap = format_money_mask(data[line].rat_fap)
            data[line].terceiros = format_money_mask(data[line].terceiros)
            data[line].total = format_money_mask(data[line].total)
            continue
        if line == 'proventos':
            for line_proventos in data[line]:
                line_proventos.sum = format_money_mask(line_proventos.sum)
            continue
        if line == 'descontos':
            for line_proventos in data[line]:
                line_proventos.sum = format_money_mask(line_proventos.sum)
            continue

    return data


@api.model
@py3o_report_extender(
    "l10n_br_hr_payroll_report.report_analytic_py3o_report")
def analytic_report(pool, cr, uid, local_context, context):
    active_model = context['active_model']
    if active_model == 'wizard.l10n_br_hr_payroll.analytic_report':
        proxy = pool['wizard.l10n_br_hr_payroll.analytic_report']
        wizard = proxy.browse(cr, uid, context['active_id'])
        busca = [
            ('company_id', '=', wizard.company_id.id),
            ('mes_do_ano', '=', wizard.mes_do_ano),
            ('ano', '=', wizard.ano),
            ('state', 'in', ['done', 'verify']),
            ('is_simulacao', '=', False),
        ]
        if wizard.tipo_de_folha == "('normal', 'rescisao')":
            busca.append(('tipo_de_folha', 'in', eval(wizard.tipo_de_folha)))
        else:
            busca.append(('tipo_de_folha', '=', eval(wizard.tipo_de_folha)))

        payslip_ids = pool['hr.payslip'].search(cr, uid, busca)

        payslips = []
        for payslip_id in payslip_ids:
            payslips += pool['hr.payslip'].browse(cr, uid, payslip_id)
    else:
        payslips = \
            pool['hr.payslip.run']\
            .browse(cr, uid, context['active_id']).slip_ids
    SQL_BUSCA_RUBRICAS = '''
    SELECT
        salary_rule.code,
        salary_rule.name,
        sum(payslip_line.quantity) as quantity,
        payslip_line.rate,
        sum(payslip_line.total),
        rule_category.code as category
    FROM
        hr_payslip payslip
        join hr_payslip_line payslip_line on payslip_line.slip_id = payslip.id
        join hr_salary_rule salary_rule on salary_rule.id =
        payslip_line.salary_rule_id
        join hr_salary_rule_category rule_category on rule_category.id =
        salary_rule.category_id
    WHERE
        payslip.mes_do_ano = {mes_do_ano}
        AND payslip.ano = {ano} 
        AND payslip.company_id = {company_id} 
        AND payslip.tipo_de_folha in {tipo_de_folha}
        AND payslip.is_simulacao = false
        AND payslip.state in ('verify', 'done')
    GROUP BY
        salary_rule.code,
        salary_rule.name,
        payslip_line.rate,
        category
    ORDER BY
        salary_rule.name;
    '''
    SQL_BUSCA_SEFIP = '''
    SELECT
        salary_rule.code,
        salary_rule.name,
        sum(payslip_line.quantity) as quantity,
        payslip_line.rate,
        sum(payslip_line.total),
        rule_category.code as category
    FROM
        hr_payslip payslip
        join hr_payslip_line payslip_line on payslip_line.slip_id = payslip.id
        join hr_salary_rule salary_rule on salary_rule.id =
        payslip_line.salary_rule_id
        join hr_salary_rule_category rule_category on rule_category.id =
        salary_rule.category_id
    WHERE
        rule_category.code = 'SEFIP' 
        AND payslip.mes_do_ano = {mes_do_ano}
        AND payslip.ano = {ano}
        AND payslip.company_id = {company_id} 
        AND payslip.tipo_de_folha in {tipo_de_folha} 
        AND payslip.is_simulacao = false
        AND payslip.state in ('verify', 'done')
    GROUP BY
        salary_rule.code,
        salary_rule.name,
        payslip_line.rate,
        category
    ORDER BY
        salary_rule.name;
    '''
    SQL_BUSCA_RUBRICAS = SQL_BUSCA_RUBRICAS.format(
        mes_do_ano=wizard.mes_do_ano,
        ano=wizard.ano,
        company_id=wizard.company_id.id,
        tipo_de_folha=wizard.tipo_de_folha
    )
    cr.execute(SQL_BUSCA_RUBRICAS)

    payslip_lines = cr.dictfetchall()
    SQL_BUSCA_SEFIP = SQL_BUSCA_SEFIP.format(
        mes_do_ano=wizard.mes_do_ano,
        ano=wizard.ano,
        company_id=wizard.company_id.id,
        tipo_de_folha=wizard.tipo_de_folha
    )
    cr.execute(SQL_BUSCA_SEFIP)

    payslip_lines_sefip = cr.dictfetchall()
    proventos = []
    descontos = []
    total_proventos = 0.00
    total_descontos = 0.00
    taxa_inss_empresa = 0.00
    taxa_rat_fap = 0.00
    taxa_terceiros = 0.00
    inss_funcionario_retido = 0.00
    inss_pro_labore_retido = 0.00
    inss_autonomo_retido = 0.00
    total_inss_retido = 0.00
    salario_familia_deducao = 0.00
    licenca_maternidade_deducao = 0.00
    valor_retencao_do_mes_deducao = 0.00
    total_inss_deducao = 0.00
    base_fgts = 0.00
    fgts = 0.00

    for rubrica in payslip_lines_sefip:
        if rubrica['code'] == 'INSS_EMPRESA':
            taxa_inss_empresa = rubrica['rate']/100
        elif rubrica['code'] == 'INSS_RAT_FAP':
            taxa_rat_fap = rubrica['rate']/100
        elif rubrica['code'] == 'INSS_OUTRAS_ENTIDADES':
            taxa_terceiros = rubrica['rate']/100

    inss_empresa_vals = \
        {
            'base': 0.0,
            'inss_empresa': 0.0,
            'rat_fap': 0.0,
            'terceiros': 0.0,
            'total': 0.0,
        }
    inss_empresa_funcionario = inss_empresa_obj(inss_empresa_vals)
    inss_empresa_pro_labore = inss_empresa_obj(inss_empresa_vals)
    inss_empresa_autonomo = inss_empresa_obj(inss_empresa_vals)
    inss_empresa_cooperativa = inss_empresa_obj(inss_empresa_vals)
    for rubrica in payslip_lines:
        # Somar os valores do INSS_EMPRESA e outros calculados nos holerites
        # Ao invés de recalcular os valores aqui
        if rubrica['code'] in ('INSS_EMPRESA_BASE', 'INSS_EMPRESA_BASE_FERIAS'):
            inss_empresa_funcionario.base += rubrica['sum']
        elif rubrica['code'] in ('INSS_EMPRESA', 'INSS_EMPRESA_FERIAS'):
            inss_empresa_funcionario.inss_empresa += rubrica['sum']
            inss_empresa_funcionario.total += rubrica['sum']
        elif rubrica['code'] in ('INSS_RAT_FAP', 'INSS_RAT_FAP_FERIAS'):
            inss_empresa_funcionario.rat_fap += rubrica['sum']
            inss_empresa_funcionario.total += rubrica['sum']
        elif rubrica['code'] in ('INSS_OUTRAS_ENTIDADES', 'INSS_OUTRAS_ENTIDADES_FERIAS'):
            inss_empresa_funcionario.terceiros += rubrica['sum']
            inss_empresa_funcionario.total += rubrica['sum']
#
#       if rubrica['code'] == 'INSS_EMPRESA':
#           inss_empresa_funcionario.base = rubrica['sum']
#           inss_empresa_funcionario.inss_empresa = \
#               rubrica['sum'] * taxa_inss_empresa
#           inss_empresa_funcionario.rat_fap = rubrica['sum'] * taxa_rat_fap
#           inss_empresa_funcionario.terceiros = \
#               rubrica['sum'] * taxa_terceiros
#           inss_empresa_funcionario.total = \
#               inss_empresa_funcionario.inss_empresa + \
#               inss_empresa_funcionario.rat_fap + \
#               inss_empresa_funcionario.terceiros
        if rubrica['category'] == 'PROVENTO':
            proventos.append(rubrica_obj(rubrica))
            total_proventos += rubrica['sum']
        elif rubrica['category'] in ['DEDUCAO', 'INSS', 'IRPF']:
            descontos.append(rubrica_obj(rubrica))
            total_descontos += rubrica['sum']
            if rubrica['category'] == 'INSS':
                inss_funcionario_retido += rubrica['sum']
        if rubrica['code'] in ['BASE_FGTS', 'BASE_FGTS_13']:
                base_fgts += rubrica['sum']
        if rubrica['code'] == 'FGTS':
            fgts += rubrica['sum']

    legal_name = payslips[0].company_id.legal_name
    endereco = \
        (payslips[0].company_id.street or "") + " " +\
        (payslips[0].company_id.street2 or "")
    telefone = payslips[0].company_id.phone
    bairro = payslips[0].company_id.district
    cidade = payslips[0].company_id.city
    estado = payslips[0].company_id.state_id.code
    cep = payslips[0].company_id.zip
    cnpj_cpf = payslips[0].company_id.cnpj_cpf
    mes_do_ano = payslips[0].mes_do_ano
    ano = payslips[0].ano

    total_bruto_inss_base = \
        inss_empresa_funcionario.base + inss_empresa_pro_labore.base + \
        inss_empresa_autonomo.base + inss_empresa_cooperativa.base
    total_bruto_inss_empresa = \
        inss_empresa_funcionario.inss_empresa + \
        inss_empresa_pro_labore.inss_empresa + \
        inss_empresa_autonomo.inss_empresa + \
        inss_empresa_cooperativa.inss_empresa
    total_bruto_inss_rat_fap = \
        inss_empresa_funcionario.rat_fap + \
        inss_empresa_pro_labore.rat_fap + \
        inss_empresa_autonomo.rat_fap + \
        inss_empresa_cooperativa.rat_fap
    total_bruto_inss_terceiros = \
        inss_empresa_funcionario.terceiros + \
        inss_empresa_pro_labore.terceiros + \
        inss_empresa_autonomo.terceiros + inss_empresa_cooperativa.terceiros
    total_bruto_inss_encargos = \
        inss_empresa_funcionario.total + \
        inss_empresa_pro_labore.total + \
        inss_empresa_autonomo.total + \
        inss_empresa_cooperativa.total

    total_inss_retido += \
        inss_funcionario_retido + inss_pro_labore_retido +\
        inss_autonomo_retido
    total_inss_deducao += \
        salario_familia_deducao + licenca_maternidade_deducao +\
        valor_retencao_do_mes_deducao

    total_liquido_inss = \
        total_bruto_inss_encargos + total_inss_retido - total_inss_deducao

    aliquota_fgts = 8
    valor_total_fgts = base_fgts * aliquota_fgts/100.00
    #valor_total_fgts = fgts
    mes_vencimento = mes_do_ano+1 if mes_do_ano < 12 else 1
    data_vencimento = \
        '20/' + ('0' + str(mes_vencimento)) if mes_vencimento < 10 else str(
            mes_vencimento) + "/" + str(ano)
    data_atual = datetime.now()
    dia_atual = \
        str(data_atual.day) + "/" + str(data_atual.month) + "/" +\
        str(data_atual.year)

    # aproveitar o selection construido no wizard do relatorio analitico
    tipo_de_folha = eval(wizard.tipo_de_folha)
    if isinstance(tipo_de_folha, tuple):
        tipo_de_folha = tipo_de_folha[0]

    data = {
        'tipo_de_folha': dict(TIPO_DE_FOLHA)[tipo_de_folha],
        'data_atual': dia_atual,
        'legal_name': legal_name,
        'endereco': endereco,
        'telefone': telefone if telefone else "",
        'bairro': bairro,
        'cidade': cidade,
        'estado': estado,
        'cep': cep,
        'cnpj_cpf': cnpj_cpf,
        'mes_do_ano': mes_do_ano,
        'ano': ano,
        'data_vencimento': data_vencimento,
        'objects': payslips,
        'proventos': proventos,
        'descontos': descontos,
        'total_proventos': total_proventos,
        'total_descontos': total_descontos,
        'total_liquido': total_proventos - total_descontos,
        'taxa_inss_empresa': taxa_inss_empresa * 100,
        'taxa_rat_fap': taxa_rat_fap * 100,
        'taxa_terceiros': taxa_terceiros * 100,
        'inss_empresa_funcionario': inss_empresa_funcionario,
        'inss_empresa_pro_labore': inss_empresa_pro_labore,
        'inss_empresa_autonomo': inss_empresa_autonomo,
        'inss_empresa_cooperativa': inss_empresa_cooperativa,
        'total_bruto_inss_base': total_bruto_inss_base,
        'total_bruto_inss_empresa': total_bruto_inss_empresa,
        'total_bruto_inss_rat_fap': total_bruto_inss_rat_fap,
        'total_bruto_inss_terceiros': total_bruto_inss_terceiros,
        'total_bruto_inss_encargos': total_bruto_inss_encargos,
        'inss_funcionario_retido': inss_funcionario_retido,
        'inss_pro_labore_retido': inss_pro_labore_retido,
        'inss_autonomo_retido': inss_autonomo_retido,
        'valor_inss':
            total_bruto_inss_empresa + total_bruto_inss_rat_fap +
            total_inss_retido,
        'total_inss_retido': total_inss_retido,
        'salario_familia_deducao': salario_familia_deducao,
        'licenca_maternidade_deducao': licenca_maternidade_deducao,
        'valor_retencao_do_mes_deducao': valor_retencao_do_mes_deducao,
        'total_inss_deducao': total_inss_deducao,
        'total_liquido_inss': total_liquido_inss,
        'base_fgts': base_fgts,
        'fgts': fgts,
        'aliquota': aliquota_fgts,
        'valor_total_fgts': valor_total_fgts,
        'empresa_abc':
            total_bruto_inss_empresa + total_bruto_inss_rat_fap +
            inss_empresa_cooperativa.total
    }
    local_context.update(process_data_format(data))
