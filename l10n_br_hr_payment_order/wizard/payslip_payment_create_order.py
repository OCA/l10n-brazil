# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from openerp import api, models, fields, _
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import TIPO_DE_FOLHA,\
    MES_DO_ANO


class PayslipPaymentCreateOrder(models.Model):
    _name = "payslip.payment.order.create"

    tipo_de_folha = fields.Selection(
        selection=TIPO_DE_FOLHA,
        string=u'Tipo de folha',
        default='normal',
    )

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        required=True,
        default=datetime.now().month,
    )

    ano = fields.Integer(
        strin="Ano",
        default=datetime.now().year,
        required=True,
    )

    entries = fields.Many2many(
        comodel_name='hr.payslip.line',
        rel='payorder_line_payslip_line_rel',
        column1='pay_id',
        column2='line_id',
        string='Entries'
    )
