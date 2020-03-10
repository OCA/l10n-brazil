# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="l10n_br_fiscal_account_tax_rel",
        colunm1="account_tax_id",
        colunm2="fiscal_tax_id",
        readonly=True,
        string="Fiscal Taxes",
    )

    @api.multi
    def compute_all(
        self,
        price_unit,
        currency=None,
        quantity=1.0,
        product=None,
        partner=None,
        cfop_id=False,
        operation_line=False,
        insurance_value=0.0,
        freight_value=0.0,
        other_costs_value=0.0,
        base_tax=0.0,
    ):
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
            price_unit, currency, quantity, product, partner
        )

        l10n_br_taxes = self.filtered(
            lambda t: t.fiscal_tax_id).mapped('fiscal_tax_id')

        account_fiscal_taxes = {
            t.fiscal_tax_id.id: t
            for t in self.filtered(lambda t: t.fiscal_tax_id)}

        l10n_br_result = l10n_br_taxes.compute_taxes(
            company=self.env.user.company_id,
            partner=partner,
            item=product,
            prince=price_unit,
            quantity=quantity,
            uom_id=product.uom_id,
            fiscal_price=price_unit,  # FIXME convert if product has uot_id
            fiscal_quantity=quantity,  # FIXME convert if product has uot_id
            uot_id=product.uot_id,  # FIXME
            ncm=product.ncm_id,
            cest=product.cest_id,
            operation_type="out",
        )

        for l10n_br_tax in l10n_br_result.values():
            account_tax = account_fiscal_taxes.get(
                l10n_br_tax.get('fiscal_tax_id'))

            if not l10n_br_tax.get('tax_include'):
                tax_result['total_included'] += l10n_br_tax.get('tax_value')

            tax_result['taxes'].append({
                'id': account_tax.id,
                'name': account_tax.name,
                'amount': l10n_br_tax.get('tax_value'),
                'base': l10n_br_tax.get('base'),
                'sequence': account_tax.sequence,
                'account_id': account_tax.account_id.id,
                'refund_account_id': account_tax.refund_account_id.id,
                'analytic': account_tax.analytic,
                'tax_include': l10n_br_tax.get('tax_include')
            })

        return tax_result
