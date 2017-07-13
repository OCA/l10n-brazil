# -*- coding: utf-8 -*-
from openerp import models, fields


class BankPaymentLine(models.Model):
    _inherit = 'bank.payment.line'

    payslip_id = fields.Many2one(
        string="Holerite",
        comodel_name="hr.payslip"
    )
