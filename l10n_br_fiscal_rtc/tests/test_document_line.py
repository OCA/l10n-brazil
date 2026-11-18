# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRtcDocumentLine(TransactionCase):
    """The line computation must use the RTC engine, and never break."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.classification = cls.env.ref("l10n_br_fiscal.tax_classification_000001")
        cls.zero_classification = cls.env.ref(
            "l10n_br_fiscal.tax_classification_200003"
        )

    def _line(self, classification=None, price_unit=1000.0, quantity=1.0, **vals):
        values = {
            "price_unit": price_unit,
            "quantity": quantity,
            **vals,
        }
        if classification:
            values["tax_classification_id"] = classification.id
        return self.env["l10n_br_fiscal.document.line"].new(values)

    def _tax_dict(self, base):
        return {
            "base_type": "percent",
            "base": base,
            "percent_amount": 0.0,
            "percent_reduction": 0.0,
            "tax_value": 0.0,
            "cst_id": False,
        }

    def test_ibs_uses_the_official_rate(self):
        """2026 test year: IBS state 0.1% and no municipal IBS."""
        line = self._line(self.classification)
        values = line._prepare_fields_ibs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "calculated")
        self.assertAlmostEqual(values["ibs_percent"], 0.1, 4)
        self.assertAlmostEqual(values["rtc_ibs_uf_value"], 1.00, 2)
        self.assertAlmostEqual(values["rtc_ibs_mun_value"], 0.00, 2)
        self.assertAlmostEqual(values["ibs_value"], 1.00, 2)
        self.assertAlmostEqual(values["ibs_base"], 1000.00, 2)
        self.assertIn("IBS_UF", values["rtc_memoria"])

    def test_cbs_uses_the_official_rate(self):
        line = self._line(self.classification)
        values = line._prepare_fields_cbs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "calculated")
        self.assertAlmostEqual(values["cbs_percent"], 0.9, 4)
        self.assertAlmostEqual(values["cbs_value"], 9.00, 2)

    def test_zero_rate_classification(self):
        """200003 carries a 100% reduction: the computed value is zero."""
        line = self._line(self.zero_classification)
        values = line._prepare_fields_ibs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "calculated")
        self.assertAlmostEqual(values["rtc_ibs_uf_value"], 0.0, 2)
        self.assertAlmostEqual(values["ibs_value"], 0.0, 2)

    def test_base_is_the_operation_value(self):
        """The RTC base is the operation value, not the legacy net base."""
        line = self._line(self.classification, price_unit=100.0, quantity=10.0)
        line.discount_value = 100.0
        line.freight_value = 50.0
        self.assertAlmostEqual(line._rtc_base_amount(), 950.0, 2)

    def test_without_classification_keeps_legacy(self):
        line = self._line()
        values = line._prepare_fields_ibs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "no_treatment")
        self.assertAlmostEqual(values["ibs_value"], 0.0, 2)

    def test_missing_rate_falls_back_on_legacy(self):
        """No 2027 rate in the official table: legacy values, no exception."""
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.env.ref("base.main_company").id,
                "document_date": "2027-06-01 10:00:00",
                "fiscal_operation_type": "out",
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            }
        )
        line = self._line(
            self.classification,
            document_id=document.id,
        )
        tax_dict = self._tax_dict(1000.0)
        tax_dict["tax_value"] = 7.77
        values = line._prepare_fields_ibs(tax_dict)
        self.assertEqual(values["rtc_status"], "error")
        # the legacy value is kept, the invoice is not blocked
        self.assertAlmostEqual(values["ibs_value"], 7.77, 2)
