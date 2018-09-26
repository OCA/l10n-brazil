# -*- coding: utf-8 -*-
# Copyright 2018 KMEE - Hendrix Costa <hendrix.costa@abgf.gov.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender
from openerp import api, fields
from pybrasil import valor
from pybrasil.data import formata_data
from pybrasil.valor.extenso import numero_por_extenso_unidade
from datetime import timedelta

@api.model
@py3o_report_extender('l10n_br_hr_payroll_report.payslip_report_recibo_ferias')
def payslip_recibo_ferias(pool, cr, uid, local_context, context):
    payslip_pool = pool['hr.payslip']
    payslip_id = payslip_pool.browse(cr, uid, context['active_id'])

    local_context['footer'] = payslip_id.company_id.rml_footer

    company_logo = payslip_id.company_id.logo
    company_nfe_logo = payslip_id.company_id.nfe_logo

    local_context['company_logo'] = \
        company_nfe_logo if company_nfe_logo else company_logo
    local_context['company_logo2'] = \
        company_nfe_logo if company_nfe_logo else company_logo
    local_context['linhas_holerites'] = payslip_id.line_resume_ids


    # Calculo da quantidade de dependentes ativos.
    qty_dependent_values = 0
    for dependente in payslip_id.employee_id.dependent_ids:
        if dependente.dependent_verification and \
                dependente.dependent_dob < payslip_id.date_from:
            qty_dependent_values += 1

    # Mensagem de dependentes
    msg_dependentes = 'OBS.: {} dependente{}'.format(
        qty_dependent_values, 's' if qty_dependent_values != 1 else '') \
        if qty_dependent_values else ''
    local_context['msg_dependentes'] = msg_dependentes

    # Mensagem de felicitações
    msg_aniversario = ''
    aniversario = str(payslip_id.ano) + payslip_id.employee_id.birthday[-6:]
    if aniversario >= payslip_id.date_from and \
            aniversario <= payslip_id.date_to:
        msg_aniversario = '\n\n\nFELIZ ANIVERSÁRIO! =) '
    local_context['msg_aniversario'] = msg_aniversario

    # Período Aquisitivo
    periodo_aquisitivo = '{} - {}'.format(
        formata_data(payslip_id.periodo_aquisitivo.inicio_aquisitivo),
        formata_data(payslip_id.periodo_aquisitivo.fim_aquisitivo)
    )
    local_context['periodo_aquisitivo'] = periodo_aquisitivo

    # Período Gozo
    periodo_gozo = '{} - {}'.format(
        formata_data(payslip_id.holidays_ferias.data_inicio),
        formata_data(payslip_id.holidays_ferias.data_fim),
    )
    local_context['periodo_gozo'] = periodo_gozo

    # Data para Retorno
    data_retorno_dt = \
        fields.Datetime.from_string(payslip_id.holidays_ferias.data_fim)
    data_retorno_dt += timedelta(days=1)
    local_context['data_retorno'] = formata_data(str(data_retorno_dt.date()))

    # Média de substituição e Base de Cálculo
    valor_salario = valor.formata_valor(payslip_id.contract_id.wage)
    media_substituicao = payslip_id.buscar_total_rubrica_payslip(
        'MEDIA_SALARIO_FERIAS')
    base_calculo = payslip_id.contract_id.wage
    if media_substituicao:
        base_calculo += media_substituicao
    msg_media_substituicao = 'MÉDIA SUBSTITUIÇÃO' if media_substituicao else ''
    valor_media_substituicao = valor.formata_valor(
        media_substituicao) if media_substituicao else ''
    local_context['valor_salario'] = valor_salario
    local_context['msg_media_substituicao'] = msg_media_substituicao
    local_context['valor_media_substituicao'] = valor_media_substituicao
    local_context['base_calculo'] = valor.formata_valor(base_calculo)

    # Mensagem de Recebimento do Adiantamento de Salário
    dias_gozo, abono_pecuniario = pool[
        'resource.calendar'].get_quantidade_dias_ferias(
        cr, uid, [],
        payslip_id.contract_id, payslip_id.date_from, payslip_id.date_to,
        context=context
    )

    if abono_pecuniario:
        total_abono_pecuniario = 0
        for line in payslip_id.line_ids:
            if line.code in ['ABONO_PECUNIARIO', '1/3_ABONO_PECUNIARIO']:
                total_abono_pecuniario += line.total

    msg_recebido = 'Recebi da empresa descrita acima a importância de R$ {}' \
                   ' ({}), correspondente a {} dias das minhas Férias ora' \
                   ' concedidas e que vou gozar de acordo com o Aviso que ' \
                   'recebi em tempo hábil. '.format(
                       payslip_id.total_folha_fmt,
                       numero_por_extenso_unidade(payslip_id.total_folha_fmt),
                       dias_gozo)

    if abono_pecuniario:
        msg_recebido += 'Recebi a importância de R$ {} ({}) do total líquido,' \
                        ' referente a {} dias de abono pecuniário. '.format(
                         valor.formata_valor(total_abono_pecuniario),
                         numero_por_extenso_unidade(total_abono_pecuniario),
                         abono_pecuniario)

    msg_recebido += 'Por ser verdade, firmo o presente recibo, ' \
                    'dando plena e geral quitação.'
    local_context['msg_recebido'] = msg_recebido
