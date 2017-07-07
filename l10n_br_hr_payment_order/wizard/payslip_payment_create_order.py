# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class PayslipPaymentCreateOrder(models.Model):
    _name = "payslip.payment.order.create"

    duedate = fields.Date(
        string='Due Date',
        required=True
    )

    entries = fields.Many2many(
        'account.move.line',
        'line_pay_payslip_rel',
        'pay_id',
        'line_id',
        string='Entries'
    )
