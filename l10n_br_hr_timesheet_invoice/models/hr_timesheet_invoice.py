# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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

    @api.v7
    def _prepare_cost_invoice_line(self, cr, uid, invoice_id, product_id, uom,
                                   user_id,
                                   factor_id, account, analytic_lines,
                                   journal_type, data, context=None):

        result = super(AccountAnalyticLine, self)._prepare_cost_invoice_line(
            cr, uid, invoice_id, product_id, uom, user_id, factor_id, account,
            analytic_lines, journal_type, data)
        invoice = self.pool.get('account.invoice').browse(
            cr, uid, [invoice_id], context)

        ctx_line = dict(context)
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
