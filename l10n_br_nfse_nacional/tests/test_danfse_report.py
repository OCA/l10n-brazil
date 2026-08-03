# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDanfseReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.doc = cls.env.ref(
            "l10n_br_nfse_nacional.demo_nfse_lc", raise_if_not_found=False
        )

    def setUp(self):
        super().setUp()
        if not self.doc:
            self.skipTest("l10n_br_nfse_nacional demo data is not installed")
        self.doc.nfse_key = "5" * 50
        self.doc.state_edoc = "autorizada"

    def test_make_pdf_generates_attachment(self):
        self.doc.make_pdf()
        self.assertTrue(self.doc.file_report_id)
        self.assertEqual(self.doc.file_report_id.mimetype, "application/pdf")

    def test_view_pdf_no_longer_raises(self):
        result = self.doc.view_pdf()
        self.assertTrue(result)
        self.assertTrue(self.doc.file_report_id)
