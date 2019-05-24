# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class AccountTax(models.Model):
    _inherit = 'account.tax'

    base_reduction = fields.Float(
        string='Redution', required=True,
        digits=dp.get_precision('Account'),
        help="Um percentual decimal em % entre 0-1.",
        default=0.00)

    amount_mva = fields.Float(
        string='MVA Percent', required=True,
        digits=dp.get_precision('Account'),
        help="Um percentual decimal em % entre 0-1.",
        default=0.00)

    amount_type = fields.Selection(
        add_selection=[('quantity', 'Quantity')])

    @api.model
    def _compute_tax(self, taxes, total_line, product, product_qty,
                     precision, base_tax=0.0):
        result = {'tax_discount': 0.0, 'taxes': []}

        for tax in taxes:
            if tax.get('amount_type') == 'weight' and product:
                product_read = self.env['product.product'].read(
                    product, ['weight_net'])
                tax['amount'] = round((product_qty * product_read.get(
                    'weight_net', 0.0)) * tax['percent'], precision)

            if base_tax:
                total_line = base_tax

            if tax.get('amount_type') == 'quantity':
                tax['amount'] = round(
                    product_qty * tax['percent'] / 100, precision)

            tax['amount'] = round(
                total_line * tax['percent'] / 100, precision)
            tax['amount'] = round(tax['amount'] * (1 - tax['base_reduction']),
                                  precision)

            if tax.get('tax_discount'):
                result['tax_discount'] += tax['amount']

            if tax['percent']:
                unrounded_base = total_line * (1 - tax['base_reduction'])
                tax['total_base'] = round(unrounded_base, precision)
                tax['total_base_other'] = round(
                    total_line - tax['total_base'], precision)
            else:
                tax['total_base'] = 0.00
                tax['total_base_other'] = 0.00

        result['taxes'] = taxes
        return result

    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0,
                    product=None, partner=None, fiscal_position=False,
                    insurance_value=0.0, freight_value=0.0,
                    other_costs_value=0.0, base_tax=0.0):
        """ Returns all information required to apply taxes
            (in self + their children in case of a tax goup).
            We consider the sequence of the parent for group of taxes.
                Eg. considering letters as taxes and alphabetic order
                as sequence :
                [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]
        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'total_tax_discount': 0.0 # Total tax out of price
            'taxes': [{               # One dict for each tax in self
                                      # and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }]
        } """

        if not currency:
            if len(self) == 0:
                company_id = self.env.user.company_id
            else:
                company_id = self[0].company_id
            currency = company_id.currency_id

        precision = currency.decimal_places or \
            self.env['decimal.precision'].precision_get('Account')
        result = super(AccountTax, self).compute_all(price_unit, currency,
                                                     quantity, product,
                                                     partner)
        totaldc = 0.0
        calculed_taxes = []

        for tax in result['taxes']:
            tax_list = [tx for tx in self if tx.id == tax['id']]
            if tax_list:
                tax_brw = tax_list[0]
            tax['domain'] = tax_brw.domain
            tax['amount_type'] = tax_brw.amount_type
            tax['percent'] = tax_brw.amount
            tax['base_reduction'] = tax_brw.base_reduction
            tax['amount_mva'] = tax_brw.amount_mva
            tax['tax_discount'] = tax_brw.tax_group_id.tax_discount

            if tax.get('domain') == 'icms':
                tax['icms_base_type'] = tax_brw.icms_base_type

            if tax.get('domain') == 'icmsst':
                tax['icms_st_base_type'] = tax_brw.icms_st_base_type

        common_taxes = [tx for tx in result['taxes'] if tx[
            'domain'] not in ['icms', 'icmsst', 'ipi', 'icmsinter',
                              'icmsfcp', 'pis', 'cofins']]

        result_tax = self._compute_tax(common_taxes, result['base'],
                                       product, quantity, precision, base_tax)

        br_taxes = [tx for tx in result['taxes'] if tx[
            'domain'] in ['icms', 'icmsst', 'ipi', 'icmsinter',
                          'icmsfcp',  'pis', 'cofins']]

        totaldc += result_tax['tax_discount']
        calculed_taxes += result_tax['taxes']

        result.update({
            'total_tax_discount': totaldc,
            'taxes': calculed_taxes + br_taxes,
        })

        return result
