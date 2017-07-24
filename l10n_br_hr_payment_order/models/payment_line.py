# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    payslip_id = fields.Many2one(
        string="Ref do Holerite",
        comodel_name="hr.payslip",
    )

    def _get_payment_line_reference(self):
        res = super(PaymentLine, self)._get_payment_line_reference()
        res.append((
            self.env['hr.payslip']._name,
            self.env['hr.payslip']._description
        ))
        return res

    @api.multi
    @api.depends('payslip_id', 'financial_id')
    def _compute_reference_id(self):

        # if not mode == 'folha':
        # return super

        for record in self:
            if record.payslip_id:
                record.reference_id = (
                    record.payslip_id._name +
                    ',' +
                    str(record.payslip_id.id)
                )
