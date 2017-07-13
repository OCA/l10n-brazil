# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class PaymentOrder(models.Model):

    _inherit = 'payment.order'

    def action_done(self):
        super(PaymentOrder, self).action_done()
        for line in self.line_ids:
            line.action_paid()
        pass


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    payslip_id = fields.Many2one(
        string="Ref do Holerite",
        comodel_name="hr.payslip",
    )
