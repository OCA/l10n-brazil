# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class AccountTax(models.Model):
    _name = 'account.tax'
    _inherit = ['account.tax.fiscal.abstract', 'account.tax']

    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0,
                    product=None, partner=None, cfop=False,
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

        core_taxes = self.filtered(lambda t: not t.fiscal_tax_id)

        tax_result = super(AccountTax, core_taxes).compute_all(
            price_unit, currency, quantity, product, partner)

        l10n_br_taxes = self.filtered(lambda t: t.fiscal_tax_id)

        l10n_br_result = l10n_br_taxes.fiscal_tax_id.compute_taxes(
            company=self.company_id,
            partner=partner,
            item=product,
            prince=price_unit,
            quantity=quantity,
            uom_id=product.uom_id,
            fiscal_price=price_unit, # FIXME convert if product has uot_id
            fiscal_quantity=quantity, # FIXME convert if product has uot_id
            uot_id=product.uot_id, # FIXME
            ncm=product.ncm_id,
            cest=product.cest_id,
            operation_type='out') # FIXME

        for l10n_br_tax in l10n_br_result:
            pass

        return tax_result
