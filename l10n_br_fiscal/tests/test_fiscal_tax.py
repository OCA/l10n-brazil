# Copyright 2020 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.tools import float_compare

from ..constants.fiscal import FINAL_CUSTOMER_NO, FINAL_CUSTOMER_YES
from ..constants.icms import ICMS_ORIGIN_DEFAULT


class TestFiscalTax(common.TransactionCase):
    def setUp(self):
        super().setUp()

    def _check_compute_taxes_result(self, test_result, compute_result, currency):
        for tax_domain in test_result["taxes"]:
            for tax_field in test_result["taxes"][tax_domain]:
                self.assertEqual(
                    float_compare(
                        test_result["taxes"][tax_domain][tax_field],
                        compute_result["taxes"][tax_domain][tax_field],
                        precision_rounding=currency.rounding,
                    ),
                    0,
                    "{} {} {} {}".format(
                        tax_domain,
                        tax_field,
                        test_result["taxes"][tax_domain][tax_field],
                        compute_result["taxes"][tax_domain][tax_field],
                    ),
                )

    def _create_compute_taxes_kwargs(self):
        return {
            "company": self.env.ref("l10n_br_base.empresa_lucro_presumido"),
            "partner": self.env.ref("l10n_br_base.res_partner_cliente5_pe"),
            "product": self.env.ref("product.product_product_12"),
            "price_unit": 3.143539,
            "quantity": 11.000,
            "uom_id": self.env.ref("uom.product_uom_unit"),
            "fiscal_price": 3.143539,
            "fiscal_quantity": 11.000,
            "uot_id": self.env.ref("uom.product_uom_unit"),
            "discount_value": 0.00,
            "insurance_value": 0.00,
            "other_value": 0.00,
            "freight_value": 0.00,
            "ii_customhouse_charges": 0.00,
            "ii_iof_value": 0.00,
            "ncm": self.env.ref("l10n_br_fiscal.ncm_72132000"),
            "nbs": False,
            "nbm": False,
            "cest": False,
            "operation_line": self.env.ref("l10n_br_fiscal.fo_venda_venda"),
            "cfop": self.env.ref("l10n_br_fiscal.cfop_6101"),
            "icmssn_range": False,
            "icms_origin": ICMS_ORIGIN_DEFAULT,
            "ind_final": FINAL_CUSTOMER_YES,
        }

    def test_compute_taxes_01(self):
        """Testa o calculo dos impostos venda para pessoa física"""

        kwargs = self._create_compute_taxes_kwargs()
        currency = kwargs["company"].currency_id

        fiscal_taxes = self.env["l10n_br_fiscal.tax"]
        fiscal_taxes |= (
            self.env.ref("l10n_br_fiscal.tax_icms_7")
            + self.env.ref("l10n_br_fiscal.tax_ipi_15")
            + self.env.ref("l10n_br_fiscal.tax_pis_0_65")
            + self.env.ref("l10n_br_fiscal.tax_cofins_3")
        )

        compute_result = fiscal_taxes.compute_taxes(**kwargs)

        test_result = {
            "taxes": {
                "ipi": {
                    "base": 34.58,
                    "base_reduction": 0.0,
                    "percent_amount": 15.0,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 5.19,
                },
                "icms": {
                    "base": 39.77,
                    "base_reduction": 0.0,
                    "percent_amount": 7.0,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 2.78,
                    "add_to_base": 5.19,
                },
                "pis": {
                    "base": 34.58,
                    "base_reduction": 0.0,
                    "percent_amount": 0.65,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 0.22,
                },
                "cofins": {
                    "base": 34.58,
                    "base_reduction": 0.0,
                    "percent_amount": 3.0,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 1.04,
                },
            }
        }

        self._check_compute_taxes_result(test_result, compute_result, currency)

    def test_compute_taxes_02(self):
        """Testa o calculo dos impostos venda para pessoa física"""

        kwargs = self._create_compute_taxes_kwargs()
        currency = kwargs["company"].currency_id
        kwargs["ind_final"] = FINAL_CUSTOMER_NO

        fiscal_taxes = self.env["l10n_br_fiscal.tax"]
        fiscal_taxes |= (
            self.env.ref("l10n_br_fiscal.tax_icms_7")
            + self.env.ref("l10n_br_fiscal.tax_ipi_15")
            + self.env.ref("l10n_br_fiscal.tax_pis_0_65")
            + self.env.ref("l10n_br_fiscal.tax_cofins_3")
        )

        compute_result = fiscal_taxes.compute_taxes(**kwargs)

        test_result = {
            "taxes": {
                "ipi": {
                    "base": 34.58,
                    "base_reduction": 0.0,
                    "percent_amount": 15.0,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 5.19,
                },
                "icms": {
                    "base": 34.58,
                    "base_reduction": 0.0,
                    "percent_amount": 7.0,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 2.42,
                    "add_to_base": 0.0,
                },
                "pis": {
                    "base": 34.58,
                    "base_reduction": 0.0,
                    "percent_amount": 0.65,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 0.22,
                },
                "cofins": {
                    "base": 34.58,
                    "base_reduction": 0.0,
                    "percent_amount": 3.0,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 1.04,
                },
            }
        }

        self._check_compute_taxes_result(test_result, compute_result, currency)
