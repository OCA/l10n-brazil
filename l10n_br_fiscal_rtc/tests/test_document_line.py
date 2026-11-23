# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import fields
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
        # The regime of a line is the one of its document: each regime is
        # tested on its own company, as in production.
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.sn_company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.document_type = cls.env.ref("l10n_br_fiscal.document_55")

    def _document(self, company=None, document_date=None):
        return self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": (company or self.company).id,
                "document_date": document_date or fields.Datetime.now(),
                "fiscal_operation_type": "out",
                "document_type_id": self.document_type.id,
            }
        )

    def _line(
        self,
        document=None,
        classification=None,
        price_unit=1000.0,
        quantity=1.0,
        **vals,
    ):
        values = {
            "document_id": (document or self._document()).id,
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
        line = self._line(classification=self.classification)
        values = line._prepare_fields_ibs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "calculated")
        self.assertAlmostEqual(values["ibs_percent"], 0.1, 4)
        self.assertAlmostEqual(values["rtc_ibs_uf_value"], 1.00, 2)
        self.assertAlmostEqual(values["rtc_ibs_mun_value"], 0.00, 2)
        self.assertAlmostEqual(values["ibs_value"], 1.00, 2)
        self.assertAlmostEqual(values["ibs_base"], 1000.00, 2)
        self.assertIn("IBS_UF", values["rtc_memoria"])

    def test_cbs_uses_the_official_rate(self):
        line = self._line(classification=self.classification)
        values = line._prepare_fields_cbs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "calculated")
        self.assertAlmostEqual(values["cbs_percent"], 0.9, 4)
        self.assertAlmostEqual(values["cbs_value"], 9.00, 2)

    def test_zero_rate_classification(self):
        """200003 carries a 100% reduction: the computed value is zero."""
        line = self._line(classification=self.zero_classification)
        values = line._prepare_fields_ibs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "calculated")
        self.assertAlmostEqual(values["rtc_ibs_uf_value"], 0.0, 2)
        self.assertAlmostEqual(values["ibs_value"], 0.0, 2)

    def test_base_is_the_operation_value(self):
        """The RTC base is the operation value, not the legacy net base."""
        line = self._line(price_unit=100.0, quantity=10.0)
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
        document = self._document(document_date="2027-06-01 10:00:00")
        line = self._line(document, classification=self.classification)
        tax_dict = self._tax_dict(1000.0)
        tax_dict["tax_value"] = 7.77
        values = line._prepare_fields_ibs(tax_dict)
        self.assertEqual(values["rtc_status"], "error")
        # the legacy value is kept, the invoice is not blocked
        self.assertAlmostEqual(values["ibs_value"], 7.77, 2)

    def test_line_without_document_uses_the_context_date(self):
        """A line without a document dates the rates on today, never crashes."""
        line = self.env["l10n_br_fiscal.document.line"].new(
            {
                "price_unit": 1000.0,
                "quantity": 1.0,
                "tax_classification_id": self.classification.id,
            }
        )
        self.assertEqual(line._rtc_tax_date(), fields.Date.context_today(line))
        values = line._prepare_fields_ibs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "calculated")

    def test_simples_nacional_line(self):
        """A Simples company uses its own rates and matrices."""
        document = self._document(
            company=self.sn_company, document_date="2027-03-10 10:00:00"
        )
        activity = self.env["l10n_br_fiscal.rtc.sn.activity"].find(
            "01", date(2027, 3, 10)
        )
        line = self._line(
            document,
            classification=self.classification,
            rtc_sn_activity_id=activity.id,
            rtc_sn_ibs_percent=1.25,
            rtc_sn_cbs_percent=2.75,
        )
        values = line._prepare_fields_ibs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "calculated_sn")
        self.assertAlmostEqual(values["ibs_value"], 12.50, 2)
        self.assertAlmostEqual(values["rtc_sn_ibs_value"], 12.50, 2)
        self.assertEqual(values["rtc_sn_revenue_type"], 1)

    def test_simples_nacional_without_activity(self):
        """No cAtivSN: the official rule does not calculate, no crash."""
        document = self._document(
            company=self.sn_company, document_date="2027-03-10 10:00:00"
        )
        line = self._line(
            document,
            classification=self.classification,
            rtc_sn_ibs_percent=1.25,
            rtc_sn_cbs_percent=2.75,
        )
        values = line._prepare_fields_ibs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "simples_nacional_activity")
        self.assertEqual(values["ibs_value"], 0.0)

    def test_simples_nacional_activity_out_of_period(self):
        """An activity not in force on the document date is not calculated,
        and that is not an error (NT 2026.005 s. 5.3.4)."""
        activity = self.env["l10n_br_fiscal.rtc.sn.activity"].create(
            {"code": "99", "name": "Not in force yet", "date_start": "2030-01-01"}
        )
        document = self._document(
            company=self.sn_company, document_date="2027-03-10 10:00:00"
        )
        line = self._line(
            document,
            classification=self.classification,
            rtc_sn_activity_id=activity.id,
            rtc_sn_ibs_percent=1.25,
            rtc_sn_cbs_percent=2.75,
        )
        values = line._prepare_fields_ibs(self._tax_dict(1000.0))
        self.assertEqual(values["rtc_status"], "not_calculated")
        self.assertEqual(values["ibs_value"], 0.0)
