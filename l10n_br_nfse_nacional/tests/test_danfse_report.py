# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import importlib

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons import l10n_br_nfse_nacional


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

    def _authorized_xml(self):
        res_items = ("tests", "nfse", "v1_00", "NFSe", "nfse-autorizada.xml")
        xml_file = importlib.resources.files(l10n_br_nfse_nacional.__name__).joinpath(
            "/".join(res_items)
        )
        return xml_file.read_bytes()

    def _attach_authorized_xml(self):
        event = self.doc.event_ids.create_event_save_xml(
            company_id=self.doc.company_id,
            environment="hml",
            event_type="0",
            xml_file=self._authorized_xml().decode(),
            document_id=self.doc,
        )
        event.set_done(
            status_code="100",
            response="Autorizado",
            protocol_date=self.doc.document_date,
            protocol_number="PROT-1",
            file_response_xml=self._authorized_xml().decode(),
        )
        self.doc.authorization_event_id = event

    def test_make_pdf_without_authorization_xml(self):
        with self.assertRaises(UserError):
            self.doc.make_pdf()

    def test_make_pdf_generates_attachment(self):
        self._attach_authorized_xml()
        self.doc.make_pdf()
        self.assertTrue(self.doc.file_report_id)
        self.assertEqual(self.doc.file_report_id.mimetype, "application/pdf")
        self.assertTrue(
            base64.b64decode(self.doc.file_report_id.datas).startswith(b"%PDF")
        )

    def test_view_pdf_returns_the_attachment(self):
        self._attach_authorized_xml()
        result = self.doc.view_pdf()
        self.assertTrue(result)
        self.assertTrue(self.doc.file_report_id)
