# -*- coding: utf-8 -*-
# Copyright 2018 KMEE - Hendrix Costa <hendrix.costa@abgf.gov.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender
from openerp import api, fields
from pybrasil.data import formata_data
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
    periodo_aquisitivo = \
        formata_data(payslip_id.periodo_aquisitivo.inicio_aquisitivo) + \
        ' - ' + \
        formata_data(payslip_id.periodo_aquisitivo.fim_aquisitivo)
    local_context['periodo_aquisitivo'] = periodo_aquisitivo

    # Período Gozo
    periodo_gozo = \
        formata_data(payslip_id.holidays_ferias.data_inicio) + \
        ' - ' + \
        formata_data(payslip_id.holidays_ferias.data_fim)
    local_context['periodo_gozo'] = periodo_gozo

    # Data para Retorno
    data_retorno_dt = \
        fields.Datetime.from_string(payslip_id.holidays_ferias.data_fim)
    data_retorno_dt += timedelta(days=1)
    local_context['data_retorno'] = formata_data(str(data_retorno_dt.date()))
