# -*- encoding: utf-8 -*-
# Copyright (C) 2017 - TODAY Albert De La Fuente - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender

@py3o_report_extender(
    "l10n_br_hr_payroll_report.report_payslip_py3o_report")
def payslip_report(pool, cr, uid, local_context, context):
    payslip_pool = pool['hr.payslip']
    payslip_id = payslip_pool.browse(cr, uid, context['active_id'])

    company_logo = payslip_id.company_id.logo
    company_nfe_logo = payslip_id.company_id.nfe_logo

    local_context['company_logo'] = \
        company_nfe_logo if company_nfe_logo else company_logo
    local_context['company_logo2'] = \
        company_nfe_logo if company_nfe_logo else company_logo

    # numero maximo de linhas por holerites, se ultrapassar esse limite será
    # dividido em 2 grupos para ser exibido em uma segunda pagina
    max_linhas = 10
    local_context['grupo_rubricas_1'] = payslip_id.line_resume_ids[:max_linhas]
    local_context['grupo_rubricas_2'] = False
    if len(payslip_id.line_resume_ids) > max_linhas:
        local_context['grupo_rubricas_2'] = \
            payslip_id.line_resume_ids[max_linhas:]
