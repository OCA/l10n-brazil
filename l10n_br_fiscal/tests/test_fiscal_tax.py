# Copyright 2020 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common

from ..constants.fiscal import (
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_II,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_SN,
    TAX_DOMAIN_ICMS_ST,
    TAX_DOMAIN_ICMS_FCP,
    TAX_DOMAIN_PIS,
    TAX_DOMAIN_PIS_ST,
    TAX_DOMAIN_PIS_WH,
    TAX_DOMAIN_COFINS,
    TAX_DOMAIN_COFINS_ST,
    TAX_DOMAIN_COFINS_WH,
    TAX_DOMAIN_ISSQN,
    TAX_DOMAIN_ISSQN_WH,
    TAX_DOMAIN_CSLL,
    TAX_DOMAIN_CSLL_WH,
    TAX_DOMAIN_IR,
    TAX_DOMAIN_IRPJ,
    TAX_DOMAIN_IRPJ_WH,
    TAX_DOMAIN_INSS,
    TAX_DOMAIN_INSS_WH,
    TAX_DOMAIN_SIMPLES,
    TAX_DOMAIN_OTHERS
)


class TestFiscalTax(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.company_normal = self.env.ref('base.main_company')
        self.company_simples = self.env.ref('empresa_simples_nacional')

        self._switch_user_company(self.env.user, self.company_normal)

    def _switch_user_company(self, user, company):
        """ Add a company to the user's allowed & set to current. """
        user.write(
            {
                "company_ids": [(6, 0, (company + user.company_ids).ids)],
                "company_id": company.id,
            }
        )

    def test_tax_ipi(self):
        """Check taxes compute IPI"""
        ipi_values = {}

        fiscal_taxes = self.env['l10n_br_fiscal.tax.group'].search(
            [('tax_domain', '=', TAX_DOMAIN_IPI)])

        for tax in fiscal_taxes:
            tax_result = tax.compute_taxes(
                company=self.company,
                partner=self.partner,
                product=self.product_id,
                price_unit=self.price_unit,
                quantity=self.quantity,
                uom_id=self.uom_id,
                fiscal_price=self.fiscal_price,
                fiscal_quantity=self.fiscal_quantity,
                uot_id=self.uot_id,
                discount_value=self.discount_value,
                insurance_value=self.insurance_value,
                other_costs_value=self.other_costs_value,
                freight_value=self.freight_value,
                ncm=self.ncm_id,
                cest=self.cest_id,
                operation_line=self.operation_line_id,
                icmssn_range=self.icmssn_range_id)
