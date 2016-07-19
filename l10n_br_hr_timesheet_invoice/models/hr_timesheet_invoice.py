# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.multi
    def invoice_cost_create(self, data):

        invoice_ids = super(AccountAnalyticLine,
                            self.with_context(type='out_invoice')
                            ).invoice_cost_create(data)

        for invoice in self.env['account.invoice'].browse(invoice_ids):
            if invoice.payment_term:
                payment_term = invoice.payment_term.id
            else:
                payment_term = False
            if invoice.partner_bank_id:
                bank = invoice.partner_bank_id.id
            else:
                bank = False

            if invoice.fiscal_category_id:
                fiscal_category_id = invoice.fiscal_category_id.id
            else:
                fiscal_category_id = False

            ctx_invoice = dict(self.env.context)
            ctx_invoice['fiscal_category_id'] = fiscal_category_id

            invoice_onchange = invoice.with_context(
                ctx_invoice).onchange_partner_id(
                'out_invoice', invoice.partner_id.id,
                invoice.date_invoice, payment_term, bank,
                invoice.company_id.id)

            ctx_line = dict(self.env.context)
            ctx_line['parent_fiscal_category_id'] = fiscal_category_id
            ctx_line['type'] = 'out_invoice'
            invoice.write(invoice_onchange['value'])
        return invoice_ids

    @api.model
    def _prepare_cost_invoice_line(
            self, invoice_id, product_id, uom, user_id, factor_id, account,
            analytic_lines, journal_type, data):

        result = super(AccountAnalyticLine, self)._prepare_cost_invoice_line(
            invoice_id, product_id, uom, user_id, factor_id, account,
            analytic_lines, journal_type, data)

        invoice = self.env['account.invoice'].browse([invoice_id])

        ctx_line = dict(self._context)
        ctx_line['parent_fiscal_category_id'] = invoice.fiscal_category_id.id
        ctx_line['type'] = 'out_invoice'

        line_onchange = invoice.invoice_line.with_context(
            ctx_line).product_id_change(
            product_id, uom,
            result['quantity'], result['name'],
            'out_invoice', invoice.partner_id.id,
            fposition_id=False, price_unit=result['price_unit'],
            currency_id=invoice.currency_id.id,
            company_id=invoice.company_id.id)

        result['invoice_line_tax_id'][0] = (
            6, 0, line_onchange['value']['invoice_line_tax_id'])
        result['fiscal_position'] = line_onchange['value']['fiscal_position']

        return result
