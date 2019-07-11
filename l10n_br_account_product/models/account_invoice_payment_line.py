# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class AccountInvoicePaymentLine(models.Model):

    _name = b'account.invoice.payment.line'
    _description = 'Dados de cobrança'
    _order = 'invoice_id, date_due, payment_id'
    _rec_name = 'number'

    payment_id = fields.Many2one(
        comodel_name='account.invoice.payment',
        string='Pagamento',
        ondelete='cascade',
    )
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        related='payment_id.invoice_id',
        store=True,
    )
    number = fields.Char(
        string='Número',
        size=60,
        readonly=True,
    )
    date_due = fields.Date(
        string='Data de vencimento',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        # related='payment_id.currency_id',
        store=True,
    )
    amount_original = fields.Float(
        string='Vr Original',
        digits=(18, 2),
        required=True,
    )
    amount_discount = fields.Float(
        string='Vr desconto',
        digits=(18, 2),
        required=True,
    )
    amount_net = fields.Float(
        string='Vr liquido',
        digits=(18, 2),
        required=True,
    )
