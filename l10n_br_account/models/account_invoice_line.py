# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids',
                 'quantity', 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        amount_tax_discount = 0.0
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(
                price, currency,
                self.quantity,
                product=self.product_id,
                partner=self.invoice_id.partner_id)

            amount_tax_discount = taxes['total_tax_discount']

        self.price_subtotal = price_subtotal_signed = \
            taxes['total_excluded'] if taxes else self.quantity * price

        self.amount_tax_discount = amount_tax_discount

        if (self.invoice_id.currency_id and self.invoice_id.company_id and
                self.invoice_id.currency_id !=
                self.invoice_id.company_id.currency_id):
            price_subtotal_signed = self.invoice_id.currency_id.compute(
                price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

    fiscal_category_id = fields.Many2one(
        codmodel_name='l10n_br_account.fiscal.category',
        string='Categoria Fiscal'
    )

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position', 
        string=u'Posição Fiscal',
        domain="[('fiscal_category_id', '=', fiscal_category_id)]"
    )

    amount_tax_discount = fields.Float(
        string='Amount Tax discount',
        store=True,
        digits=dp.get_precision('Account'),
        readonly=True,
        compute='_compute_price',
        oldname='price_tax_discount'
    )
