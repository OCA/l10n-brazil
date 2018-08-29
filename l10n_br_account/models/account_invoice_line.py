# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids',
                 'quantity', 'product_id', 'invoice_id.partner_id',
                 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        for record in self:
            currency = (
                record.invoice_id and record.invoice_id.currency_id or None)
            price = record.price_unit * (1 - (record.discount or 0.0) / 100.0)
            taxes = False
            amount_tax_discount = 0.0
            if record.invoice_line_tax_ids:
                taxes = record.invoice_line_tax_ids.compute_all(
                    price, currency,
                    record.quantity,
                    product=record.product_id,
                    partner=record.invoice_id.partner_id)

                amount_tax_discount = taxes['total_tax_discount']

            record.price_subtotal = price_subtotal_signed = \
                taxes['total_excluded'] if taxes else record.quantity * price

            record.amount_tax_discount = amount_tax_discount

            if (record.invoice_id.currency_id and record.invoice_id.company_id
                and record.invoice_id.currency_id !=
                    record.invoice_id.company_id.currency_id):
                price_subtotal_signed = record.invoice_id.currency_id.compute(
                    price_subtotal_signed,
                    record.invoice_id.company_id.currency_id)
            sign = record.invoice_id.type in [
                'in_refund', 'out_refund'] and -1 or 1
            record.price_subtotal_signed = price_subtotal_signed * sign

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
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
