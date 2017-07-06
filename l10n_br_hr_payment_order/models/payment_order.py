# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class PaymentOrder(models.Model):

    _inherit = 'payment.order'


class PaymentLine(models.Model):
    _inherit = 'payment.line'

    payslip_id = fields.Many2one(
        string="Ref do Holerite",
        comodel_name="hr.payslip",
    )
