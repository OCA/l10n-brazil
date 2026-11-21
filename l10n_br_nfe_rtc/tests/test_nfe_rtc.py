# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNfeRtcExport(TransactionCase):
    """The NF-e must export the IBS split of the RTC engine."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env["res.partner"].create(
            {"name": "RTC Partner", "is_company": True}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "RTC Product", "list_price": 1000.0}
        )
        cls.classification = cls.env.ref("l10n_br_fiscal.tax_classification_000001")
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "fiscal_operation_type": "out",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
            }
        )

    def _line(self):
        return self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 1000.0,
                "tax_classification_id": self.classification.id,
            }
        )

    def _export_ibscbs(self, line):
        return line.with_context(
            spec_schema="nfe", spec_version="40"
        )._export_m2o_via_tag_hooks("nfe40_IBSCBS", self.env["nfe.40.imposto"])

    def test_split_ibs_state_and_municipality(self):
        line = self._line()
        line.write(
            {
                "rtc_status": "calculated",
                "ibs_base": 1000.0,
                "ibs_value": 1.0,
                "rtc_ibs_uf_percent": 0.05,
                "rtc_ibs_uf_value": 0.50,
                "rtc_ibs_mun_percent": 0.05,
                "rtc_ibs_mun_value": 0.50,
                "rtc_cbs_percent": 8.8,
                "rtc_cbs_value": 88.0,
                "cbs_value": 88.0,
            }
        )
        result = self._export_ibscbs(line)
        self.assertEqual(result.gIBSCBS.gIBSUF.pIBSUF, "0.0500")
        self.assertEqual(result.gIBSCBS.gIBSUF.vIBSUF, "0.50")
        self.assertEqual(result.gIBSCBS.gIBSMun.pIBSMun, "0.0500")
        self.assertEqual(result.gIBSCBS.gIBSMun.vIBSMun, "0.50")
        self.assertEqual(result.gIBSCBS.vIBS, "1.00")
        self.assertEqual(result.gIBSCBS.gCBS.vCBS, "88.00")

    def test_legacy_export_untouched(self):
        """Without a calculated RTC line the historical mapping is kept."""
        line = self._line()
        line.write({"ibs_value": 10.0, "ibs_percent": 10.0, "ibs_base": 100.0})
        result = self._export_ibscbs(line)
        self.assertEqual(result.gIBSCBS.gIBSUF.pIBSUF, "10.0000")
        self.assertEqual(result.gIBSCBS.gIBSUF.vIBSUF, "10.00")
        self.assertEqual(result.gIBSCBS.gIBSMun.pIBSMun, "0.0000")
