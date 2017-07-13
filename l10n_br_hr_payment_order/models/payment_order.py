# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    payslip_id = fields.Many2one(
        string="Ref do Holerite",
        comodel_name="hr.payslip",
    )

    # def action_done(self):
    #     self.status = 'done'
    #
    # # FIXME
    # def action_paid(self):
    #     self.status = 'paid'
    #
    # # Caso de retorno
    # def verify_error(self):
    #     pass
