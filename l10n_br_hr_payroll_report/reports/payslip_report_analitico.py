# -*- encoding: utf-8 -*-
# Copyright (C) 2017  KMEE
# Copyright (C) 2018  ABGF
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime

from openerp import api, _
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import TIPO_DE_FOLHA
from openerp.addons.report_py3o.py3o_parser import py3o_report_extender
from openerp.exceptions import Warning


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


class Totalizador(object):
    def __init__(self):
        self.proventos = []
        self.descontos = []
        self.total_proventos = 0.00
        self.total_descontos = 0.00
        self.total_liquido = 0.00
        self.inss_empresa_funcionario = 0.00
        self.inss_empresa_pro_labore = 0.00
        self.inss_empresa_autonomo = 0.00
        self.inss_empresa_cooperativa = 0.00
        self.total_bruto_inss_base = 0.00
        self.total_bruto_inss_empresa = 0.00
        self.total_bruto_inss_rat_fap = 0.00
        self.total_bruto_inss_terceiros = 0.00
        self.total_bruto_inss_encargos = 0.00
        self.inss_funcionario_retido = 0.00
        self.inss_pro_labore_retido = 0.00
        self.inss_autonomo_retido = 0.00
        self.valor_inss = 0.00
        self.total_inss_retido = 0.00
        self.salario_familia_deducao = 0.00
        self.licenca_maternidade_deducao = 0.00
        self.valor_retencao_do_mes_deducao = 0.00
        self.total_inss_deducao = 0.00
        self.total_liquido_inss = 0.00
        self.base_fgts = 0.00
        self.fgts = 0.00
        self.aliquota = 0.00
        self.valor_total_fgts = 0.00
        self.empresa_abc = 0.00

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

def totalizadores_linhas_holerites(payslip_lines, payslip_autonomo_ids=[]):
    """
    :param data: 
    :param payslip_lines: 
    :return: 
    """
    proventos = []
    descontos = []
    total_proventos = 0.00
    total_descontos = 0.00
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

    inss_empresa_vals = {
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
        elif rubrica['code'] in \
                ('INSS_OUTRAS_ENTIDADES', 'INSS_OUTRAS_ENTIDADES_FERIAS'):
            inss_empresa_funcionario.terceiros += rubrica['sum']
            inss_empresa_funcionario.total += rubrica['sum']

        if rubrica['category'] == 'PROVENTO':
            proventos.append(rubrica_obj(rubrica))
            total_proventos += rubrica['sum']

        elif rubrica['category'] in ['DEDUCAO', 'INSS', 'IRPF']:
            descontos.append(rubrica_obj(rubrica))
            total_descontos += rubrica['sum']

            # Totalizar INSS descontado de todos funcionários
            #
            # INSS DA competencia traz informação do inss de mes anterior
            if rubrica['category'] == 'INSS':

                # Nao contabilizar essas rubricas quebradas no analitico:
                #  Competencia seguinte nao deverá sair no analitico
                #  competencia Atual será substituida pela rubrica da
                #  INSS_FERIAS_DA_COMPETENCIA para que consiga pegat tb mes ant
                if rubrica['code'] not in \
                        ['INSS_COMPETENCIA_SEGUINTE_FERIAS',
                         'INSS_COMPETENCIA_ATUAL',
                         'INSS_COMPETENCIA_SEGUINTE',
                         'INSS_FERIAS_COMPETENCIA_ANTERIOR']:
                    inss_funcionario_retido += rubrica['sum']

        # Totalizar O INSS da Competencia que esta em um rubrica de referencia
        # Essa rubrica trará INSS de mes anterior adiantado em férias
        if rubrica['code'] in ['INSS_FERIAS_DA_COMPETENCIA']:
            inss_funcionario_retido += rubrica['sum']

        # FGTS a maior, valores serão negativos e nao deverão compor FGTS
        if rubrica['sum'] > 0:

            if rubrica['code'] in ['BASE_FGTS', 'BASE_FGTS_13']:
                base_fgts += rubrica['sum']

            if rubrica['code'] in ['FGTS']:
                fgts += rubrica['sum']

        if rubrica['code'] in ['LIC_MATERNIDADE', 'LIC_MATERNIDADE_13']:
            licenca_maternidade_deducao = rubrica['sum']

    # INSS dos autonomos
    for slip_id in payslip_autonomo_ids:
        for line_id in slip_id.line_ids:
            if line_id.category_id.code in ['INSS']:
                inss_autonomo_retido += line_id.total
            if line_id.salary_rule_id.compoe_base_INSS:
                inss_empresa_autonomo.base += line_id.total
                # Calcular manualmente o INSS para exibicao do analitico.
                # PS Futuramente implementaremos o cálculo automatico do
                # INSS / INSS_PATRONAL para os autonomos
                inss_empresa_autonomo.inss_empresa += line_id.total * 0.225
                inss_empresa_autonomo.total += line_id.total * 0.225

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

    totalizador = Totalizador()
    totalizador.proventos = proventos
    totalizador.descontos= descontos
    totalizador.total_proventos= total_proventos
    totalizador.total_descontos= total_descontos
    totalizador.total_liquido= total_proventos - total_descontos
    totalizador.inss_empresa_funcionario= inss_empresa_funcionario
    totalizador.inss_empresa_pro_labore= inss_empresa_pro_labore
    totalizador.inss_empresa_autonomo= inss_empresa_autonomo
    totalizador.inss_empresa_cooperativa= inss_empresa_cooperativa
    totalizador.total_bruto_inss_base= total_bruto_inss_base
    totalizador.total_bruto_inss_empresa= total_bruto_inss_empresa
    totalizador.total_bruto_inss_rat_fap= total_bruto_inss_rat_fap
    totalizador.total_bruto_inss_terceiros= total_bruto_inss_terceiros
    totalizador.total_bruto_inss_encargos= total_bruto_inss_encargos
    totalizador.inss_funcionario_retido= inss_funcionario_retido
    totalizador.inss_pro_labore_retido= inss_pro_labore_retido
    totalizador.inss_autonomo_retido= inss_autonomo_retido
    totalizador.total_inss_retido= total_inss_retido
    totalizador.salario_familia_deducao= salario_familia_deducao
    totalizador.licenca_maternidade_deducao= licenca_maternidade_deducao
    totalizador.valor_retencao_do_mes_deducao= valor_retencao_do_mes_deducao
    totalizador.total_inss_deducao= total_inss_deducao
    totalizador.total_liquido_inss= total_liquido_inss
    totalizador.base_fgts= base_fgts
    totalizador.fgts= fgts
    totalizador.aliquota= aliquota_fgts
    totalizador.valor_total_fgts= valor_total_fgts
    totalizador.valor_inss = \
        total_bruto_inss_empresa + total_bruto_inss_rat_fap + \
        total_inss_retido,
    totalizador.empresa_abc = \
        total_bruto_inss_empresa + total_bruto_inss_rat_fap + \
        inss_empresa_cooperativa.total,
    
    return totalizador

def informacoes_adicionais(data, payslips):
    """
    Dado os holerites do lote, extrair informações adicionais 
    :param data:
    :return:
    """
    empresa_id = payslips[0].company_id
    legal_name = empresa_id.legal_name
    telefone = empresa_id.phone
    bairro = empresa_id.district
    cidade = empresa_id.city
    estado = empresa_id.state_id.code
    cep = empresa_id.zip
    cnpj_cpf = empresa_id.cnpj_cpf
    endereco = (empresa_id.street or "") + " " + (empresa_id.street2 or "")
    mes_do_ano = payslips[0].mes_do_ano
    ano = payslips[0].ano

    company_logo = empresa_id.logo
    company_nfe_logo = empresa_id.nfe_logo

    mes_vencimento = mes_do_ano + 1 if mes_do_ano < 12 else 1
    data_vencimento = \
        '20/' + ('0' + str(mes_vencimento)) if mes_vencimento < 10 else str(
            mes_vencimento) + "/" + str(ano)
    data_atual = datetime.now()
    dia_atual = \
        str(data_atual.day) + "/" + str(data_atual.month) + "/" + \
        str(data_atual.year)

    data.update({
        'object': payslips[0],
        'legal_name': legal_name,
        'endereco': endereco,
        'telefone': telefone if telefone else "",
        'bairro': bairro,
        'cidade': cidade,
        'estado': estado,
        'cep': cep,
        'cnpj_cpf': cnpj_cpf,
        'mes_do_ano': '{:02d}'.format(mes_do_ano),
        'ano': ano,
        'data_atual': dia_atual,
        'data_vencimento': data_vencimento,
        'company_logo': company_nfe_logo if company_nfe_logo else company_logo,
        'company_logo2': company_nfe_logo if company_nfe_logo else company_logo,
    })

def totalizadores_sefip(data, payslip_lines_sefip):
    """
    Calcular totalizadores das rubricas de referencia do SEFIp
    """
    taxa_inss_empresa = 0.00
    taxa_rat_fap = 0.00
    taxa_terceiros = 0.00

    for rubrica in payslip_lines_sefip:
        if rubrica['code'] == 'INSS_EMPRESA':
            taxa_inss_empresa = rubrica['rate']/100
        elif rubrica['code'] == 'INSS_RAT_FAP':
            taxa_rat_fap = rubrica['rate']/100
        elif rubrica['code'] == 'INSS_OUTRAS_ENTIDADES':
            taxa_terceiros = rubrica['rate']/100

    data.update({
        'taxa_inss_empresa': taxa_inss_empresa * 100,
        'taxa_rat_fap': taxa_rat_fap * 100,
        'taxa_terceiros': taxa_terceiros * 100,
    })

    return data

def get_SQL_analitico(mes_do_ano, ano, company_id, tipo_de_folha, sefip):
    """
    Gerar uma consulta SQL para relatório analitico
    :return: string com a consulta SQL
    """
    SQL_BUSCA = '''
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
            {sefip}
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

    SQL_sefip = "rule_category.code = 'SEFIP' AND " if sefip else ""

    return SQL_BUSCA.format(
        sefip=SQL_sefip,
        mes_do_ano=mes_do_ano,
        ano=ano,
        company_id=company_id,
        tipo_de_folha=tipo_de_folha
    )

def get_payslip_lines(cr, mes_do_ano, ano, company_id, tipo_de_folha, sefip=False):
    """
    Buscar as linhas de holerites de acordo com os parametros ja agrupando e
    totalizando
    """
    SQL = get_SQL_analitico(mes_do_ano, ano, company_id, tipo_de_folha, sefip)
    cr.execute(SQL)
    payslip_lines = cr.dictfetchall()
    return payslip_lines

@api.model
@py3o_report_extender(
    "l10n_br_hr_payroll_report.report_analytic_py3o_report")
def analytic_report(pool, cr, uid, local_context, context):
    """
    :return:
    """
    data = {}
    payslips_rescisoes = []

    proxy = pool['wizard.l10n_br_hr_payroll.analytic_report']
    wizard = proxy.browse(cr, uid, context['active_id'])

    #
    # GET Holerites
    #
    busca = [
        ('company_id', '=', wizard.company_id.id),
        ('mes_do_ano', '=', wizard.mes_do_ano),
        ('ano', '=', wizard.ano),
        ('state', 'in', ['done', 'verify']),
        ('is_simulacao', '=', False),
    ]

    if wizard.tipo_de_folha == "('normal', 'rescisao', 'rescisao_complementar')":

        # Holerites normais
        domain = busca + [('tipo_de_folha', '=', eval(wizard.tipo_de_folha)[0])]
        payslip_ids = pool['hr.payslip'].search(cr, uid, domain)
        payslips = pool['hr.payslip'].browse(cr, uid, payslip_ids)
        # Linhas dos holerites para totalizadores
        payslip_lines_holerites = get_payslip_lines(
            cr, wizard.mes_do_ano, wizard.ano, wizard.company_id.id,
            "('normal')")

        # Rescisoes
        domain = busca + [('tipo_de_folha', 'in', [eval(wizard.tipo_de_folha)[1], eval(wizard.tipo_de_folha)[2]])]
        payslip_rescisoes_ids = pool['hr.payslip'].search(cr, uid, domain)
        payslips_rescisoes = \
            pool['hr.payslip'].browse(cr, uid, payslip_rescisoes_ids)
        # Linhas das rescisoes para totalizadores
        payslip_lines_rescisoes = get_payslip_lines(
            cr, wizard.mes_do_ano, wizard.ano, wizard.company_id.id,
            "('rescisao', 'rescisao_complementar')")

    else:
        busca.append(('tipo_de_folha', '=', eval(wizard.tipo_de_folha)))
        payslip_ids = pool['hr.payslip'].search(cr, uid, busca)
        payslips = pool['hr.payslip'].browse(cr, uid, payslip_ids)
        payslip_lines_holerites = get_payslip_lines(
            cr, wizard.mes_do_ano, wizard.ano, wizard.company_id.id,
            wizard.tipo_de_folha)
        payslip_lines_rescisoes = []

    # Todas as linhas para Totalizadores gerais
    payslip_lines_total = get_payslip_lines(
            cr, wizard.mes_do_ano, wizard.ano, wizard.company_id.id,
            wizard.tipo_de_folha)

    # Holerites
    data.update({'objects': payslips})

    #
    #  Rescisoes
    if payslips_rescisoes:
        data.update({'payslips_rescisoes': payslips_rescisoes,
                     'exibir_rescisoes': True})
    else:
        data.update({'payslips_rescisoes': [],
                     'exibir_rescisoes': False})

    # 
    # GET Autonomos
    # Funcionários autonomos - sem vinculo possuem um payslip a parte
    payslip_line_autonomos_ids = pool['hr.payslip.autonomo'].search(
        cr, uid, busca)
    payslip_autonomo_ids = pool['hr.payslip.autonomo'].browse(
        cr, uid, payslip_line_autonomos_ids)
    
    # 
    # Totalizadores
    #
    total_holerites = totalizadores_linhas_holerites\
        (payslip_lines_holerites, payslip_autonomo_ids)
    data.update({'totalizadores_holerites': total_holerites})

    total_rescisoes = totalizadores_linhas_holerites(payslip_lines_rescisoes)
    data.update({'totalizadores_rescisoes': total_rescisoes})

    total = totalizadores_linhas_holerites(
        payslip_lines_total, payslip_autonomo_ids)
    data.update(total.__dict__)

    #
    #  Totalizadores do SEFIP
    # Linhas dos holerites para totalizadores do SEFIP
    payslip_lines_sefip = get_payslip_lines(
        cr, wizard.mes_do_ano, wizard.ano, wizard.company_id.id,
        wizard.tipo_de_folha, sefip=True)

    totalizadores_sefip(data, payslip_lines_sefip)

    #
    # Informações Adicionais no Ánalitico - Dados da Empresa
    #
    if not payslips:
        raise Warning(
            _('Warning!'),
            _('Nenhum Holerite confirmado encontrado no período indicado!')
        )
    informacoes_adicionais(data, payslips)

    # Aproveitar o selection construido no wizard do relatorio analitico
    tipo_de_folha = eval(wizard.tipo_de_folha)
    if isinstance(tipo_de_folha, tuple):
        tipo_de_folha = tipo_de_folha[0]
    data.update({'tipo_de_folha': dict(TIPO_DE_FOLHA)[tipo_de_folha]})

    # Rotina para formatar valores e data
    local_context.update(process_data_format(data))
