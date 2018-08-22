# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _compute_tax(self, taxes, total_line,
                     product, product_qty, precision):
        result = {'tax_discount': 0.0, 'taxes': []}

        for tax in taxes:

            tax['amount'] = round(
                tax['amount'] * (1 - tax['base_reduction']), precision)

            if tax.get('tax_discount'):
                result['tax_discount'] += tax['amount']
            if tax['amount_type'] == 'percent':
                tax['total_base'] = round(
                    total_line * (1 - tax['base_reduction']), precision)
                tax['total_base_other'] = round(
                    total_line - tax['total_base'], precision)
            else:
                tax['total_base'] = 0.00
                tax['total_base_other'] = 0.00

        result['taxes'] = taxes
        return result

    @api.multi
    def compute_all(self, price_unit, currency=None,
                    quantity=1.0, product=None, partner=None):
        """Returns all information required to apply taxes
        (in self + their children in case of a tax goup).

        We consider the sequence of the parent for group of taxes.
            Eg. considering letters as taxes and alphabetic order as sequence:
            [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]

        Args:
            price_unit (float): Product price unit
            currency (ResCurrency): Currency
            quantity (float): Product quantity
            product (ProductProduct): Product
            partner (ResPartner): Partner

        Returns: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'taxes': [{
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }]
        """

        precision = self.env['decimal.precision'].precision_get('Account')
        if not currency:
            if len(self) == 0:
                company_id = self.env.user.company_id
            else:
                company_id = self[0].company_id
            currency = company_id.currency_id
        taxes = self
        result = super(AccountTax, self).compute_all(price_unit,
                                                     currency=currency,
                                                     quantity=quantity,
                                                     product=product,
                                                     partner=partner)

        totaldc = 0.0
        calculed_taxes = []

        for tax in result['taxes']:
            tax_list = [tx for tx in taxes if tx.id == tax['id']]
            if tax_list:
                tax_brw = tax_list[0]
            tax['group'] = tax_brw.tax_group_id.name
            tax['type'] = tax_brw.type_tax_use
            # TODO - check parent compute
            tax['percent'] = tax_brw.amount
            tax['amount_type'] = tax_brw.amount_type
            tax['base_reduction'] = tax_brw.base_reduction
            tax['amount_mva'] = tax_brw.amount_mva
            tax['tax_discount'] = tax_brw.tax_discount

        common_taxes = [tx for tx in result['taxes'] if tx['group']]
        result_tax = self._compute_tax(
            common_taxes, result['total_excluded'],
            product, quantity, precision)
        totaldc += result_tax['tax_discount']
        calculed_taxes += result_tax['taxes']

        return {
            'total_excluded': result['total_excluded'],
            'total_included': result['total_included'],
            'total_tax_discount': totaldc,
            'taxes': calculed_taxes
        }
