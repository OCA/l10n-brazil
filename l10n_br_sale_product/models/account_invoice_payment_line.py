# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class AccountInvoicePaymentLine(models.Model):

    _inherit = 'account.invoice.payment.line'

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        related='payment_id.sale_id',
        store=True,
    )
