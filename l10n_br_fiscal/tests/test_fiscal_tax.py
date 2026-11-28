# Copyright 2020 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase
from odoo.tools import float_compare

from ..constants.fiscal import FINAL_CUSTOMER_NO, FINAL_CUSTOMER_YES
from ..constants.icms import ICMS_ORIGIN_DEFAULT


class TestFiscalTax(TransactionCase):
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

        self.assertEqual(
            float_compare(
                compute_result["amount_included"],
                test_result["amount_included"],
                precision_rounding=currency.rounding,
            ),
            0,
            f"Amount included diff: "
            f"{compute_result['amount_included']} - "
            f"{test_result['amount_included']}.",
        )
        self.assertEqual(
            float_compare(
                compute_result["amount_not_included"],
                test_result["amount_not_included"],
                precision_rounding=currency.rounding,
            ),
            0,
            f"Amount not included diff: "
            f"{compute_result['amount_not_included']} - "
            f"{test_result['amount_not_included']}.",
        )
        self.assertEqual(
            float_compare(
                compute_result["amount_withholding"],
                test_result["amount_withholding"],
                precision_rounding=currency.rounding,
            ),
            0,
            f"Amount Withholding diff: "
            f"{compute_result['amount_withholding']} - "
            f"{test_result['amount_withholding']}.",
        )
        self.assertEqual(
            float_compare(
                compute_result["estimate_tax"],
                test_result["estimate_tax"],
                precision_rounding=currency.rounding,
            ),
            0,
            f"Estimate Tax diff: "
            f"{compute_result['estimate_tax']} - "
            f"{test_result['estimate_tax']}.",
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
            + self.env.ref("l10n_br_fiscal.tax_ibs_0_1")
            + self.env.ref("l10n_br_fiscal.tax_cbs_0_9")
        )

        compute_result = fiscal_taxes.compute_taxes(**kwargs)

        test_result = {
            "amount_included": 4.34,
            "amount_not_included": 5.19,
            "amount_withholding": 0.0,
            "estimate_tax": 0.0,
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
                "ibs": {
                    "base": 30.54,
                    "base_reduction": 0.0,
                    "percent_amount": 0.10,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 0.03,
                },
                "cbs": {
                    "base": 30.54,
                    "base_reduction": 0.0,
                    "percent_amount": 0.90,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 0.27,
                },
            },
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
            "amount_included": 3.68,
            "amount_not_included": 5.19,
            "amount_withholding": 0.0,
            "estimate_tax": 0.0,
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
            },
        }

        self._check_compute_taxes_result(test_result, compute_result, currency)

    def test_compute_taxes_03(self):
        """Testa o calculo dos impostos de compra - entrada de importação"""

        kwargs = self._create_compute_taxes_kwargs()
        currency = kwargs["company"].currency_id

        kwargs["partner"] = self.env.ref("base.res_partner_12")
        kwargs["price_unit"] = 49.63180
        kwargs["quantity"] = 5.00
        kwargs["fiscal_price"] = 49.63180
        kwargs["fiscal_quantity"] = 5.00
        kwargs["insurance_value"] = 0.00
        kwargs["other_value"] = 74.87
        kwargs["freight_value"] = 0.00
        kwargs["ii_customhouse_charges"] = 7.72
        kwargs["ii_iof_value"] = 0.00
        kwargs["operation_line"] = self.env.ref("l10n_br_fiscal.fo_compras_compras")
        kwargs["cfop"] = self.env.ref("l10n_br_fiscal.cfop_3101")

        fiscal_taxes = self.env["l10n_br_fiscal.tax"]
        fiscal_taxes |= (
            self.env.ref("l10n_br_fiscal.tax_icms_17")
            + self.env.ref("l10n_br_fiscal.tax_ii_10")
            + self.env.ref("l10n_br_fiscal.tax_ipi_15")
            + self.env.ref("l10n_br_fiscal.tax_pis_monofasico_2_10")
            + self.env.ref("l10n_br_fiscal.tax_cofins_monofasico_10_68")
        )

        compute_result = fiscal_taxes.compute_taxes(**kwargs)

        test_result = {
            "amount_included": 128.90,
            "amount_not_included": 40.95,
            "amount_withholding": 0.0,
            "estimate_tax": 0.0,
            "taxes": {
                "ii": {
                    "base": 248.16,
                    "base_reduction": 0.0,
                    "percent_amount": 10.0,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 24.82,
                },
                "ipi": {
                    "base": 272.98,
                    "base_reduction": 0.0,
                    "percent_amount": 15.0,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 40.95,
                },
                "icms": {
                    "base": 425.73,
                    "base_reduction": 0.0,
                    "percent_amount": 17.00,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 72.37,
                    "add_to_base": 105.20,
                    "remove_from_base": 0.0,
                },
                "pis": {
                    "base": 248.16,
                    "base_reduction": 0.0,
                    "percent_amount": 2.10,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 5.21,
                },
                "cofins": {
                    "base": 248.16,
                    "base_reduction": 0.0,
                    "percent_amount": 10.68,
                    "percent_reduction": 0.0,
                    "value_amount": 0.0,
                    "tax_value": 26.50,
                },
            },
        }

        self._check_compute_taxes_result(test_result, compute_result, currency)

    def test_ibs_cbs_rate_reduction(self):
        """IBS and CBS keep the full base and reduce the rate (cClassTrib 200032
        case of the official RTC calculator: vBC 200.00, vIBSUF 0.08, vCBS 0.72)"""
        kwargs = self._create_compute_taxes_kwargs()
        kwargs.update(fiscal_price=200.0, fiscal_quantity=1.0)
        fiscal_taxes = self.env.ref("l10n_br_fiscal.tax_ibs_0_1_red_60") + self.env.ref(
            "l10n_br_fiscal.tax_cbs_0_9_red_60"
        )
        taxes = fiscal_taxes.compute_taxes(**kwargs)["taxes"]
        self.assertEqual(taxes["ibs"]["base"], 200.0)
        self.assertEqual(taxes["ibs"]["tax_value"], 0.08)
        self.assertEqual(taxes["cbs"]["base"], 200.0)
        self.assertEqual(taxes["cbs"]["tax_value"], 0.72)

    def test_icmsst_forces_icms_cst_10(self):
        """When ICMS ST also applies to the line, the ICMS tax CST must be
        forced to "10" (Tributada e com cobrança do ICMS por substituição
        tributária), instead of the ICMS tax's own default CST.

        Uses "Empresa Lucro Presumido" because ``map_fiscal_taxes`` only
        consults the ICMS Regulation when ``company.tax_framework`` is the
        "normal" framework (Simples Nacional companies never reach that
        step) - this demo company already has both the normal framework
        and an ICMS Regulation configured.
        """
        company = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        partner = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        product = self.env.ref("product.product_product_1")
        line = self.env.ref("l10n_br_fiscal.fo_venda_revendast")

        product.tax_icms_or_issqn = "icms"
        product.fiscal_type = "00"
        product.ncm_id = self.env.ref("l10n_br_fiscal.ncm_48191000")
        product.cest_id = self.env.ref("l10n_br_fiscal.cest_2112300")

        mapping_result = line.map_fiscal_taxes(
            company=company,
            partner=partner,
            product=product,
            nbm=self.env["l10n_br_fiscal.nbm"],
            nbs=self.env["l10n_br_fiscal.nbs"],
            city_taxation_code=self.env["l10n_br_fiscal.city.taxation.code"],
            national_taxation_code=self.env["l10n_br_fiscal.national.taxation.code"],
            service_type=self.env["l10n_br_fiscal.service.type"],
        )
        self.assertIn("icmsst", mapping_result["taxes"])

        fiscal_taxes = self.env["l10n_br_fiscal.tax"]
        for tax in mapping_result["taxes"].values():
            fiscal_taxes |= tax

        compute_result = fiscal_taxes.compute_taxes(
            company=company,
            partner=partner,
            product=product,
            price_unit=100.00,
            quantity=1.00,
            fiscal_price=100.00,
            fiscal_quantity=1.00,
            operation_line=line,
            cfop=mapping_result["cfop"],
            ncm=product.ncm_id,
            cest=product.cest_id,
        )

        self.assertEqual(compute_result["taxes"]["icms"]["cst_id"].code, "10")

    def test_withholding_revenue_code(self):
        """The federal taxes withheld at source carry the code of their DARF."""
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.tax_irpj_wh_1").revenue_code, "1708"
        )
        self.assertEqual(
            self.env.ref("l10n_br_fiscal.tax_csll_wh_1").revenue_code, "5952"
        )

    def test_withheld_irpj_in_the_withholding_group(self):
        """Every IRPJ RET tax is in the group of the IRPJ withheld at source."""
        group = self.env.ref("l10n_br_fiscal.tax_group_irpj_wh")
        taxes = self.env["l10n_br_fiscal.tax"].search([("name", "=like", "IRPJ RET%")])
        self.assertIn(self.env.ref("l10n_br_fiscal.tax_irpj_wh_4_6"), taxes)
        self.assertEqual(taxes.tax_group_id, group)

    def test_federal_body_withholding_taxes(self):
        """A federal body withholds IR, CSLL, PIS and COFINS in one DARF per
        code (IN RFB 1.234/2012, Annex I): one tax per group and code."""
        ref = self.env.ref
        expected = {
            "6190": ("tax_irpj_wh_4_6", 4.8),
            "6147": ("tax_irpj_wh_1_2_6147", 1.2),
            "6175": ("tax_irpj_wh_2_4_6175", 2.4),
            "6188": ("tax_irpj_wh_2_4_6188", 2.4),
        }
        for code, (irpj, percent) in expected.items():
            taxes = {
                "tax_group_irpj_wh": (ref(f"l10n_br_fiscal.{irpj}"), percent),
                "tax_group_csll_wh": (ref(f"l10n_br_fiscal.tax_csll_wh_1_{code}"), 1.0),
                "tax_group_pis_wh": (
                    ref(f"l10n_br_fiscal.tax_pis_wh_0_65_{code}"),
                    0.65,
                ),
                "tax_group_cofins_wh": (
                    ref(f"l10n_br_fiscal.tax_cofins_wh_3_{code}"),
                    3.0,
                ),
            }
            for group, (tax, tax_percent) in taxes.items():
                self.assertEqual(tax.revenue_code, code, tax.name)
                self.assertEqual(tax.tax_group_id, ref(f"l10n_br_fiscal.{group}"))
                self.assertAlmostEqual(tax.percent_amount, tax_percent)
                self.assertIn(f"({code})", tax.name)
        self.assertEqual(
            ref("l10n_br_fiscal.tax_irpj_wh_4_6").name, "IRPJ RET 4,8% (6190)"
        )

    def test_private_csrf_revenue_code(self):
        """The PIS and the COFINS withheld by a private company go in the DARF
        5952 of the CSRF, the same of the CSLL."""
        for xmlid in ("tax_pis_wh_0_65", "tax_cofins_wh_3"):
            tax = self.env.ref(f"l10n_br_fiscal.{xmlid}")
            self.assertEqual(tax.revenue_code, "5952")
            self.assertNotIn("(", tax.name)
