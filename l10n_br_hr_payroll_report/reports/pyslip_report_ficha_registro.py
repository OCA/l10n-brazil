# -*- coding: utf-8 -*-
# Copyright 2019 ABGF - Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender
from openerp import api


# @api.model
# @py3o_report_extender('l10n_br_hr_payroll.reports.payslip_report_ficha_registro')
# def payslip_ficha_registro(pool, cr, uid, local_context, context):
#     companylogo = \
#         pool['hr.payslip'] \
#         .browse(cr, uid, context['active_id']).company_id.logo
#     d = {'companylogo': companylogo}
#     local_context.update(d)
