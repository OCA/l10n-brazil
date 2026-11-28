# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase
from odoo.tools import float_compare

from odoo.addons.l10n_br_fiscal.constants.fiscal import FINAL_CUSTOMER_YES
from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_ORIGIN_DEFAULT


class TestFiscalTaxManual(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.currency = cls.env.company.currency_id
        cls.document = cls.env.ref("l10n_br_fiscal.demo_nfe_same_state")
        cls.line = cls.document.fiscal_line_ids.filtered("icms_tax_id")[0]

    def _float_eq(self, value, expected, msg=None):
        self.assertEqual(
            float_compare(value, expected, precision_rounding=self.currency.rounding),
            0,
            msg or f"{value} != {expected}",
        )

    def test_automatic_calculation_without_manual_values(self):
        original_value = self.line.icms_value
        # Just touching the line without filling any manual field must not
        # change the automatically computed value.
        self.line._compute_tax_fields()
        self._float_eq(self.line.icms_value, original_value)

    def test_manual_value_overrides_computed_value(self):
        manual_value = self.line.icms_value + 1.00
        self.line.icms_value_manual = manual_value
        self._float_eq(self.line.icms_value, manual_value)

    def test_manual_base_recomputes_tax_value(self):
        manual_base = self.line.icms_base + 10.00
        expected_value = manual_base * self.line.icms_percent / 100
        self.line.icms_base_manual = manual_base
        self._float_eq(self.line.icms_base, manual_base)
        self._float_eq(self.line.icms_value, expected_value)

    def test_manual_base_and_value_together(self):
        manual_base = self.line.icms_base + 10.00
        manual_value = self.line.icms_value + 1.00
        self.line.icms_base_manual = manual_base
        self.line.icms_value_manual = manual_value
        self._float_eq(self.line.icms_base, manual_base)
        self._float_eq(self.line.icms_value, manual_value)

    def test_clearing_manual_value_restores_automatic_calculation(self):
        original_value = self.line.icms_value
        self.line.icms_value_manual = original_value + 1.00
        self.line.icms_value_manual = 0.0
        self._float_eq(self.line.icms_value, original_value)

    def test_prepare_br_manual_tax_dict_only_returns_filled_values(self):
        self.line.icms_value_manual = 1.00
        manual_values = self.line._prepare_br_manual_tax_dict()
        self.assertEqual(set(manual_values.keys()), {"icms_value_manual"})
        self.assertEqual(manual_values["icms_value_manual"], 1.00)

    def test_manual_values_are_copied_with_fiscal_values(self):
        self.line.icms_value_manual = 1.00
        copy = self.line.copy()
        self.assertEqual(copy.icms_value_manual, 1.00)

    def test_imported_document_is_not_recomputed(self):
        original_value = self.line.icms_value
        self.document.imported_document = True
        self.line.icms_value_manual = original_value + 1.00
        self._float_eq(self.line.icms_value, original_value)

    def test_manual_value_on_cbs_and_ibs(self):
        cbs_line = self.document.fiscal_line_ids.filtered("cbs_tax_id")[:1]
        ibs_line = self.document.fiscal_line_ids.filtered("ibs_tax_id")[:1]
        if cbs_line:
            cbs_line.cbs_value_manual = cbs_line.cbs_value + 1.00
            self._float_eq(cbs_line.cbs_value, cbs_line.cbs_value_manual)
        if ibs_line:
            ibs_line.ibs_value_manual = ibs_line.ibs_value + 1.00
            self._float_eq(ibs_line.ibs_value, ibs_line.ibs_value_manual)

    def test_tax_manual_allowed_follows_fiscal_operation_line(self):
        # tax_manual_allowed (which drives the view's visibility of the
        # manual fields) mirrors the fiscal operation line configuration,
        # and the manual fields keep working regardless of it: the flag is
        # only about reducing clutter on screen, not about blocking the
        # override.
        operation_line = self.line.fiscal_operation_line_id
        operation_line.allow_tax_manual = False
        self.assertFalse(self.line.tax_manual_allowed)

        operation_line.allow_tax_manual = True
        self.assertTrue(self.line.tax_manual_allowed)

        operation_line.allow_tax_manual = False
        self.line.icms_value_manual = self.line.icms_value + 1.00
        self._float_eq(self.line.icms_value, self.line.icms_value_manual)

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

    def test_compute_taxes_reads_manual_values_from_context(self):
        kwargs = self._create_compute_taxes_kwargs()
        fiscal_taxes = self.env.ref("l10n_br_fiscal.tax_icms_7")
        result = fiscal_taxes.with_context(
            l10n_br_manual_tax_values={"icms_value_manual": 9.99}
        ).compute_taxes(**kwargs)
        self._float_eq(result["taxes"]["icms"]["tax_value"], 9.99)

    def test_manual_base_on_domain_without_specific_compute_method(self):
        # cbs/ibs have no dedicated _compute_<domain> method on
        # l10n_br_fiscal.tax, so they fall back to the generic _compute_tax /
        # _compute_tax_base, which the manual override also covers.
        kwargs = self._create_compute_taxes_kwargs()
        fiscal_taxes = self.env.ref("l10n_br_fiscal.tax_ibs_0_1")
        result = fiscal_taxes.with_context(
            l10n_br_manual_tax_values={"ibs_value_manual": 1.23}
        ).compute_taxes(**kwargs)
        self._float_eq(result["taxes"]["ibs"]["tax_value"], 1.23)
