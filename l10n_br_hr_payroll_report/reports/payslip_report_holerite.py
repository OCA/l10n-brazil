# -*- encoding: utf-8 -*-
# Copyright (C) 2017 - TODAY Albert De La Fuente - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender

@py3o_report_extender(
    "l10n_br_hr_payroll_report.report_payslip_py3o_report")
def payslip_report(pool, cr, uid, local_context, context):
    payslip_pool = pool['hr.payslip']

    company_logo = \
        payslip_pool.browse(cr, uid, context['active_id']).company_id.logo

    company_nfe_logo =\
        payslip_pool.browse(cr, uid, context['active_id']).company_id.nfe_logo

    local_context['company_logo'] = \
        company_nfe_logo if company_nfe_logo else company_logo
