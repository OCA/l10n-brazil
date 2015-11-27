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
    def invoice_cost_create(self):

        invoice_ids = super(
            AccountAnalyticLine, self.with_context(type='out_invoice')
        ).create()

        for invoice in self.env['account.invoice'].browse(invoice_ids):

            invoice_lines = invoice.invoice_line.search(
                [('invoice_id', '=', invoice.id)]).ids

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

            invoice_onchange = invoice.onchange_partner_id(
                [invoice.id], 'out_invoice', invoice.partner_id.id,
                invoice.date_invoice, payment_term, bank,
                invoice.company_id.id, fiscal_category_id)

            parent_fposition_id = invoice_onchange['value']['fiscal_position']

            for line in invoice_lines:
                line_onchange = line.product_id_change(
                    line.product_id.id, line.uos_id.id,
                    line.quantity, line.name,
                    'out_invoice', invoice.partner_id.id,
                    fposition_id=False, price_unit=line.price_unit,
                    currency_id=invoice.currency_id.id,
                    company_id=invoice.company_id.id,
                    parent_fiscal_category_id=fiscal_category_id,
                    parent_fposition_id=parent_fposition_id)
                line.write(line_onchange['value'])
            invoice.write(invoice_onchange['value'])
        return invoice_ids
