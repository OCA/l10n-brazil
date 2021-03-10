# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='l10n_br_fiscal_account_tax_rel',
        colunm1='account_tax_id',
        colunm2='fiscal_tax_id',
        string='Fiscal Taxes',
    )

    @api.multi
    def compute_all(
        self,
        price_unit,
        currency=None,
        quantity=1.0,
        product=None,
        partner=None,
        fiscal_taxes=None,
        operation_line=False,
        ncm=None,
        nbs=None,
        nbm=None,
        cest=None,
        discount_value=None,
        insurance_value=None,
        other_value=None,
        freight_value=None,
        fiscal_price=None,
        fiscal_quantity=None,
        uot=None,
        icmssn_range=None,
        icms_origin=None
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

        taxes_results = super().compute_all(
            price_unit, currency, quantity, product, partner)

        if not fiscal_taxes:
            fiscal_taxes = self.env['l10n_br_fiscal.tax']

        product = product or self.env['product.product']

        # FIXME Should get company from document?
        fiscal_taxes_results = fiscal_taxes.compute_taxes(
            company=self.env.user.company_id,
            partner=partner,
            product=product,
            price_unit=price_unit,
            quantity=quantity,
            uom_id=product.uom_id,
            fiscal_price=fiscal_price or price_unit,
            fiscal_quantity=fiscal_quantity or quantity,
            uot_id=uot or product.uot_id,
            ncm=ncm or product.ncm_id,
            nbs=nbs or product.nbs_id,
            nbm=nbm or product.nbm_id,
            cest=cest or product.cest_id,
            discount_value=discount_value,
            insurance_value=insurance_value,
            other_value=other_value,
            freight_value=freight_value,
            operation_line=operation_line,
            icmssn_range=icmssn_range,
            icms_origin=icms_origin or product.icms_origin)

        account_taxes_by_domain = {}
        for tax in self:
            tax_domain = tax.tax_group_id.fiscal_tax_group_id.tax_domain
            account_taxes_by_domain.update({tax.id: tax_domain})

        for account_tax in taxes_results['taxes']:
            fiscal_tax = fiscal_taxes_results['taxes'].get(
                account_taxes_by_domain.get(account_tax.get('id'))
            )

            if fiscal_tax:
                tax = self.filtered(lambda t: t.id == account_tax.get('id'))
                if not fiscal_tax.get('tax_include') and not tax.deductible:
                    taxes_results['total_included'] += fiscal_tax.get(
                        'tax_value')

                account_tax.update({
                    'id': account_tax.get('id'),
                    'name': '{0} ({1})'.format(
                        account_tax.get('name'),
                        fiscal_tax.get('name')
                    ),
                    'amount': fiscal_tax.get('tax_value'),
                    'base': fiscal_tax.get('base'),
                    'tax_include': fiscal_tax.get('tax_include'),
                })

                if tax.deductible:
                    account_tax.update({
                        'amount': fiscal_tax.get('tax_value', 0.0) * -1,
                    })

        return taxes_results
