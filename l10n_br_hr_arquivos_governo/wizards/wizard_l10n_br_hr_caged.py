# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import (
    TIPO_DE_FOLHA,
    MES_DO_ANO,
)


class WizardL10n_br_hr_payrollAnalytic_report(models.TransientModel):

    _name = 'wizard.l10n_br_hr_arquivos_governo.caged'

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        default=fields.Date.from_string(fields.Date.today()).month
    )

    ano = fields.Integer(
        string=u'Ano',
        default=fields.Date.from_string(fields.Date.today()).year
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Empresa',
    )

    @api.multi
    def doit(self):
        print ('boa')
        return True
        # return self.env['report'].get_action(
        #     self, "l10n_br_hr_payroll_report_py3o.report_analyticreport")
