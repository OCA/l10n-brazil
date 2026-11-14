# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    FINAL_CUSTOMER_NO,
    FINAL_CUSTOMER_YES,
)
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


class TestFiscalTaxManual(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_fiscal_fixture_files(cls.env)
        # The fiscal comments format numbers with pt_BR (grouping, decimal
        # comma). Odoo 18 res.lang.format() only serves active languages,
        # and CI runs without demo data where pt_BR is not activated.
        cls.env["res.lang"]._activate_lang("pt_BR")
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente5_pe")
        cls.product = cls.env.ref("product.product_product_12")
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
            }
        )
        cls.line = cls._create_line(cls.document)

    @classmethod
    def _create_line(cls, document):
        """Same values as test_compute_taxes_02 of l10n_br_fiscal's
        test_fiscal_tax.py, so the automatic values are a known baseline:
        base 34.58, ICMS 7% 2.42, IPI 15% 5.19, PIS 0.65% 0.22, COFINS 3% 1.04.
        """
        line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "company_id": document.company_id.id,
                "partner_id": document.partner_id.id,
                "fiscal_operation_type": document.fiscal_operation_type,
                "fiscal_operation_id": document.fiscal_operation_id.id,
                "product_id": cls.product.id,
                "price_unit": 3.143539,
                "quantity": 11.0,
            }
        )
        line.fiscal_operation_line_id = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        line.cfop_id = cls.env.ref("l10n_br_fiscal.cfop_6101")
        line.ind_final = FINAL_CUSTOMER_NO
        line.fiscal_tax_ids = (
            cls.env.ref("l10n_br_fiscal.tax_icms_7")
            + cls.env.ref("l10n_br_fiscal.tax_ipi_15")
            + cls.env.ref("l10n_br_fiscal.tax_pis_0_65")
            + cls.env.ref("l10n_br_fiscal.tax_cofins_3")
        )
        return line

    def _compute_taxes_kwargs(self, ind_final=FINAL_CUSTOMER_NO):
        uom = self.env.ref("uom.product_uom_unit")
        return {
            "company": self.company,
            "partner": self.partner,
            "product": self.product,
            "price_unit": 3.143539,
            "quantity": 11.0,
            "uom_id": uom,
            "fiscal_price": 3.143539,
            "fiscal_quantity": 11.0,
            "uot_id": uom,
            "ncm": self.env.ref("l10n_br_fiscal.ncm_72132000"),
            "nbs": False,
            "nbm": False,
            "cest": False,
            "operation_line": self.env.ref("l10n_br_fiscal.fo_venda_venda"),
            "cfop": self.env.ref("l10n_br_fiscal.cfop_6101"),
            "icms_origin": "0",
            "ind_final": ind_final,
        }

    def assertMonetary(self, value, expected):
        self.assertAlmostEqual(
            value, expected, places=self.company.currency_id.decimal_places
        )

    def test_automatic_calculation_without_manual_values(self):
        """Without manual values the core calculation is unchanged: the
        value is the automatic base times the tax percentage."""
        self.assertTrue(self.line.icms_base)
        self.assertMonetary(
            self.line.icms_value,
            self.line.icms_base * self.line.icms_percent / 100,
        )
        self.assertMonetary(
            self.line.ipi_value,
            self.line.ipi_base * self.line.ipi_percent / 100,
        )

    def test_manual_value_overrides_computed_value(self):
        """Writing a manual value recomputes the line (it is a dependency of
        _compute_tax_fields) and replaces only that tax value, keeping the
        automatically computed base and the other taxes untouched."""
        icms_base_before = self.line.icms_base
        ipi_value_before = self.line.ipi_value
        self.line.icms_value_manual = 99.90
        self.assertMonetary(self.line.icms_value, 99.90)
        self.assertMonetary(self.line.icms_base, icms_base_before)
        self.assertMonetary(self.line.ipi_value, ipi_value_before)

    def test_manual_base_recomputes_tax_value(self):
        """The tax value is computed from the manual base."""
        percent = self.line.icms_percent
        self.line.icms_base_manual = 1000.00
        self.assertMonetary(self.line.icms_base, 1000.00)
        self.assertMonetary(self.line.icms_value, 1000.00 * percent / 100)

    def test_manual_base_and_value(self):
        self.line.write({"pis_base_manual": 200.00, "pis_value_manual": 5.00})
        self.assertMonetary(self.line.pis_base, 200.00)
        self.assertMonetary(self.line.pis_value, 5.00)

    def test_clearing_manual_value_restores_automatic_calculation(self):
        cofins_value_before = self.line.cofins_value
        self.line.cofins_value_manual = 50.00
        self.assertMonetary(self.line.cofins_value, 50.00)
        self.line.cofins_value_manual = 0.0
        self.assertMonetary(self.line.cofins_value, cofins_value_before)

    def test_manual_value_is_used_in_line_totals(self):
        """IPI is not included in the price: its manual value must be the
        one added to the line's taxes not included."""
        amount_before = self.line.amount_tax_not_included
        ipi_value_before = self.line.ipi_value
        self.line.ipi_value_manual = 10.00
        self.assertMonetary(
            self.line.amount_tax_not_included,
            amount_before + (10.00 - ipi_value_before),
        )

    def test_imported_document_is_not_recomputed(self):
        """Imported documents keep their values, like in the core."""
        self.document.imported_document = True
        self.line.icms_value_manual = 99.90
        self.assertMonetary(self.line.icms_value, 2.42)

    def test_manual_values_are_copied_with_fiscal_values(self):
        """_prepare_br_fiscal_dict copies every mixin field, so manual values
        follow the line from sale/purchase orders to the invoice."""
        self.line.issqn_wh_value_manual = 7.50
        vals = self.line._prepare_br_fiscal_dict()
        self.assertEqual(vals["issqn_wh_value_manual"], 7.50)

    def test_prepare_br_manual_tax_dict_only_returns_filled_values(self):
        self.assertEqual(self.line._prepare_br_manual_tax_dict(), {})
        self.line.icms_value_manual = 15.00
        self.assertEqual(
            self.line._prepare_br_manual_tax_dict(), {"icms_value_manual": 15.00}
        )

    def test_compute_taxes_reads_manual_values_from_context(self):
        taxes = self.env.ref("l10n_br_fiscal.tax_pis_0_65").with_context(
            l10n_br_manual_tax_values={"pis_value_manual": 12.34}
        )
        result = taxes.compute_taxes(**self._compute_taxes_kwargs())
        self.assertMonetary(result["taxes"]["pis"]["tax_value"], 12.34)

    def test_manual_ipi_value_enters_icms_base_for_final_customer(self):
        """For a final customer the core adds the IPI value to the ICMS base
        (test_compute_taxes_01: base 34.58 + IPI 5.19 = 39.77), so a manual
        IPI value must be the one added."""
        taxes = self.env.ref("l10n_br_fiscal.tax_icms_7") + self.env.ref(
            "l10n_br_fiscal.tax_ipi_15"
        )
        result = taxes.compute_taxes(
            ipi_value_manual=10.00,
            **self._compute_taxes_kwargs(ind_final=FINAL_CUSTOMER_YES),
        )
        self.assertMonetary(result["taxes"]["ipi"]["tax_value"], 10.00)
        self.assertMonetary(result["taxes"]["icms"]["base"], 44.58)

    def test_manual_value_on_cbs_and_ibs(self):
        """The tax reform's CBS/IBS domains already have base/value fields
        on the mixin (unlike IS, which has no dedicated fields yet), so
        they get a manual override just like the other domains."""
        taxes = self.env.ref("l10n_br_fiscal.tax_cbs_0_9") + self.env.ref(
            "l10n_br_fiscal.tax_ibs_0_1"
        )
        result = taxes.compute_taxes(
            cbs_value_manual=3.21,
            ibs_base_manual=250.00,
            **self._compute_taxes_kwargs(),
        )
        self.assertMonetary(result["taxes"]["cbs"]["tax_value"], 3.21)
        self.assertMonetary(result["taxes"]["ibs"]["base"], 250.00)

    def test_manual_base_on_domain_without_specific_method(self):
        """ISSQN has no _compute_issqn method: it goes through the generic
        _compute_tax/_compute_tax_base, which must honor the manual base."""
        issqn_tax = self.env["l10n_br_fiscal.tax"].search(
            [("tax_domain", "=", "issqn"), ("percent_amount", ">", 0)], limit=1
        )
        self.assertTrue(issqn_tax, "No ISSQN tax found in the fiscal data")
        result = issqn_tax.compute_taxes(
            issqn_base_manual=500.00, **self._compute_taxes_kwargs()
        )
        self.assertMonetary(result["taxes"]["issqn"]["base"], 500.00)
        self.assertMonetary(
            result["taxes"]["issqn"]["tax_value"],
            500.00 * issqn_tax.percent_amount / 100,
        )

    def test_icmsst_manual_value_is_not_reduced_by_icms(self):
        """The core subtracts the line's own ICMS from the ICMS ST value;
        that must not change a manually informed ICMS ST value."""
        product = self.env.ref("product.product_product_1")
        partner = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        operation_line = self.env.ref("l10n_br_fiscal.fo_venda_revendast")
        product.write(
            {
                "tax_icms_or_issqn": "icms",
                "fiscal_type": "00",
                "ncm_id": self.env.ref("l10n_br_fiscal.ncm_48191000").id,
                "cest_id": self.env.ref("l10n_br_fiscal.cest_2112300").id,
            }
        )
        mapping = operation_line.map_fiscal_taxes(
            company=self.company,
            partner=partner,
            product=product,
            nbm=self.env["l10n_br_fiscal.nbm"],
            nbs=self.env["l10n_br_fiscal.nbs"],
            city_taxation_code=self.env["l10n_br_fiscal.city.taxation.code"],
            national_taxation_code=self.env["l10n_br_fiscal.national.taxation.code"],
            service_type=self.env["l10n_br_fiscal.service.type"],
        )
        self.assertIn("icmsst", mapping["taxes"])
        taxes = self.env["l10n_br_fiscal.tax"]
        for tax in mapping["taxes"].values():
            taxes |= tax

        result = taxes.compute_taxes(
            company=self.company,
            partner=partner,
            product=product,
            price_unit=100.0,
            quantity=1.0,
            fiscal_price=100.0,
            fiscal_quantity=1.0,
            operation_line=operation_line,
            cfop=mapping["cfop"],
            ncm=product.ncm_id,
            cest=product.cest_id,
            icmsst_value_manual=42.00,
        )
        self.assertMonetary(result["taxes"]["icmsst"]["tax_value"], 42.00)
