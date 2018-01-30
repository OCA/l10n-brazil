# -*- coding: utf-8 -*-
# Copyright 2017-TODAY - Akretion (http://www.akretion.com).
#  @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_mode_id = fields.Many2one(
        comodel_name='payment.mode', string="Payment Mode",)

