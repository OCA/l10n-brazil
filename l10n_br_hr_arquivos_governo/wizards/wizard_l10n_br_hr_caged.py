# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

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
        default=lambda self: self.env.user.company_id or '',
    )

    @api.multi
    def doit(self):

        data_mes = \
            datetime.strptime(str(self.mes_do_ano) +
                              '-' + str(self.ano), '%m-%Y')
        ultimo_dia_do_mes = \
            data_mes + relativedelta(months=1) - relativedelta(days=1)

        primeiro_dia_do_mes = \
            ultimo_dia_do_mes - relativedelta(months=1) + relativedelta(days=1)

        contrato_model = self.env['hr.contract']

        domain = [
            ('date_start', '>=', ultimo_dia_do_mes),
            ('date_start', '>=', primeiro_dia_do_mes)
        ]
        contratacoes = contrato_model.search(domain)

        domain = [
            ('date_end', '>=', ultimo_dia_do_mes),
            ('date_end', '>=', primeiro_dia_do_mes)
        ]
        demissoes = contrato_model.search(domain)


        return True
