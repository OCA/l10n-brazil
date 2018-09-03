# -*- encoding: utf-8 -*-
# Copyright (C) 2017 - TODAY Albert De La Fuente - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender

@py3o_report_extender(
    "l10n_br_hr_payroll_report.report_payslip_py3o_report")
def payslip_report(pool, cr, uid, local_context, context):
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

    local_context['data_pagamento'] = \
        payslip_id.payment_order_id.date_scheduled or ''

    # Competencia
    competencia = dict(payslip_id._fields.get('mes_do_ano').selection).get(
        payslip_id.mes_do_ano) + ' de ' + str(payslip_id.ano)
    local_context['competencia'] = competencia

    # Calculo da quantidade de dependentes ativos.
    qty_dependent_values = 0
    for dependente in payslip_id.employee_id.dependent_ids:
        if dependente.dependent_verification and \
                dependente.dependent_dob < payslip_id.date_from:
                    qty_dependent_values += 1

    # Bloco para montar as observacoes do Holerite
    msg_dependentes = 'OBS.: Nº Dependente{} IR: {}'.format(
        's' if qty_dependent_values != 1 else '', qty_dependent_values) \
        if qty_dependent_values else ''
    local_context['msg_dependentes'] = msg_dependentes

    # Mensagem de felcitações
    msg_aniversario = ''
    aniversario = str(payslip_id.ano) + payslip_id.employee_id.birthday[-6:]
    if aniversario >= payslip_id.date_from and \
            aniversario <= payslip_id.date_to:
        msg_aniversario = '\n\n\n  FELIZ ANIVERSÁRIO! =) '
    local_context['msg_aniversario'] = msg_aniversario
