# -*- coding: utf-8 -*-
#    KMEE, KM Enterprising Engineering
#    Copyright (C) 2014 - Michell Stuttgart Faria (<http://www.kmee.com.br>).
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class SaleAdvancePaymentInvoice(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.one
    def _get_line_qty(self, line):
        if line.order_id.invoice_quantity == 'order':
            if line.product_uos:
                return line.product_uos_qty or 0.0
        return line.product_uom_qty

    @api.one
    def _get_line_uom(self, line):
        if line.order_id.invoice_quantity == 'order':
            if line.product_uos:
                return line.product_uos.id
        return line.product_uom.id

    @api.one
    def _prepare_advance_invoice_vals(self):

        # Lista de campos
        result = super(
            SaleAdvancePaymentInvoice, self)._prepare_advance_invoice_vals()

        if self._context is None:
            context = {}

        sale_obj = self.pool['sale.order']
        wizard = self.browse(self._ids[0])
        # get invoice type
        payment_type = wizard.advance_payment_method

        for res in result:
            for sale in sale_obj.browse([res[0]]):

                # Verificamos o tipo de fatura
                if payment_type == 'percentage':
                    percent = wizard.amount / 100.0
                else:
                    percent = wizard.amount / sale.amount_gross

                # Aux list of invoice
                list_invoice = []

                # Invoice dict in res
                invoice_dict = res[1]['invoice_line'][0][2]

                for order_line in sale.order_line:

                    # Objeto sale.order.line
                    order_line_obj = self.pool.get('sale.order.line')

                    res_aux = {}
                    res_aux = (order_line_obj.
                               l10n_br_sale_prepare_order_line_invoice_line(
                        order_line, res_aux))

                    res_aux = order_line_obj. \
                        l10n_br_sale_product_prepare_order_line_invoice_line(
                        order_line, res_aux)

                    tax_list_id = []

                    uosqty = self._get_line_qty(order_line)
                    uos_id = self._get_line_uom(order_line)

                    # Add the ID of tax of order line
                    for tax in order_line.tax_id:
                        tax_list_id.append(tax.id)

                    # create the invoice
                    inv_line_values = {
                        'name': order_line.name,
                        'origin': invoice_dict['origin'],
                        'account_id': invoice_dict['account_id'],
                        'price_unit': order_line.price_unit,
                        'quantity': (percent * uosqty) or 1.0,
                        'discount': invoice_dict['discount'],
                        'uos_id': uos_id,
                        'product_id': order_line.product_id.id,
                        'invoice_line_tax_id': [(6, 0, tax_list_id)],
                        'account_analytic_id': invoice_dict.get(
                            'account_analytic_id'),
                        'fiscal_category_id': res_aux.get(
                            'fiscal_category_id'),
                        'fiscal_position': res_aux.get('fiscal_position'),
                        'cfop_id': res_aux.get('cfop_id'),
                    }

                    list_invoice.append((0, 0, inv_line_values))

                res[1]['invoice_line'] = list_invoice
                res[1]['comment'] = invoice_dict['name']
        return result
