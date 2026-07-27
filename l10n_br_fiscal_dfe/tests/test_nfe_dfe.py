# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import zipfile
from io import BytesIO
from unittest import mock

from xsdata.formats.dataclass.transports import DefaultTransport

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.tests.test_dfe import (
    response_sucesso_individual,
    response_sucesso_multiplos,
)


def _bytes(string):
    return string.encode("utf-8") if isinstance(string, str) else string


class TestNFeDFe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

    def _search_dfe(self):
        return self.env["l10n_br_fiscal_dfe.dfe"].search(
            [("company_id", "=", self.company.id)]
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_download_document_proc_nfe(self, _mock_post):
        _mock_post.return_value = _bytes(response_sucesso_individual)

        self.company.dfe_search_documents()
        dfe_docs = self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id)]
        )
        for doc in dfe_docs:
            doc.import_document()

        self.assertEqual(len(self._search_dfe()), 1)
        access_key = "35200159594315000157550010000000012062777161"
        fiscal_doc = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", access_key)], limit=1
        )
        self.assertTrue(fiscal_doc, "Fiscal document should be created after import")
        self.assertEqual(fiscal_doc.document_key, access_key)
        self.assertEqual(_mock_post.call_count, 1)

    @mock.patch.object(DefaultTransport, "post")
    def test_search_dfe_success(self, _mock_post):
        _mock_post.return_value = _bytes(response_sucesso_multiplos)

        self.company.dfe_search_documents()
        dfe_records = self._search_dfe()
        self.assertTrue(dfe_records)

        dfe_sorted = dfe_records.sorted(lambda record: record.nsu or "")
        dfe1, dfe2 = dfe_sorted

        self.assertEqual(dfe1.company_id, self.company)
        self.assertEqual(
            dfe1.access_key, "31201010588201000105550010038421171838422178"
        )
        self.assertEqual(dfe1.dfe_nfe_document_type, "dfe_nfe_summary")
        self.assertEqual(dfe1.nsu, "000000000000200")
        self.assertEqual(
            dfe1.display_name,
            "31201010588201000105550010038421171838422178 - Resumo da NF-e",
        )
        self.assertEqual(dfe1.dfe_document_id.color_status, "blue")
        self.assertEqual(dfe1.dfe_document_id.emitter, "ZAP GRAFICA E EDITORA EIRELI")
        self.assertEqual(dfe1.dfe_document_id.vat, "10.588.201/0001-05")
        self.assertEqual(
            dfe1.dfe_document_id.display_name,
            "31201010588201000105550010038421171838422178",
        )
        self.assertEqual(
            dfe1.dfe_document_id.access_key,
            "31201010588201000105550010038421171838422178",
        )

        self.assertEqual(dfe2.company_id, self.company)
        self.assertEqual(
            dfe2.access_key, "35200159594315000157550010000000012062777161"
        )
        self.assertEqual(dfe2.dfe_nfe_document_type, "dfe_nfe_complete")
        self.assertEqual(dfe2.dfe_document_id.emitter, "TESTE - Simples Nacional")
        self.assertEqual(dfe2.dfe_document_id.document_amount, 14.0)
        self.assertEqual(dfe2.dfe_document_id.vat, "59.594.315/0001-57")
        self.assertEqual(
            dfe2.dfe_document_id.access_key,
            "35200159594315000157550010000000012062777161",
        )
        self.assertEqual(
            dfe2.display_name,
            "35200159594315000157550010000000012062777161 - NF-e Completa",
        )
        self.assertEqual(dfe2.dfe_document_id.color_status, "green")
        self.assertEqual(
            dfe2.dfe_document_id.display_name,
            "35200159594315000157550010000000012062777161",
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_generate_danfe(self, _mock_post):
        _mock_post.return_value = _bytes(response_sucesso_individual)
        self.company.dfe_search_documents()
        dfe_record = self._search_dfe()[0]

        result = dfe_record.dfe_document_id.make_pdf()

        self.assertEqual(result["type"], "ir.actions.act_url")
        self.assertTrue(result["url"].startswith("/web/content/"))
        self.assertIn("download=true", result["url"])

    @mock.patch.object(DefaultTransport, "post")
    def test_download_documents(self, _mock_post):
        _mock_post.return_value = _bytes(response_sucesso_multiplos)

        self.company.dfe_search_documents()
        dfe_sorted = self._search_dfe().sorted(lambda record: record.nsu or "")
        dfe1, dfe2 = dfe_sorted

        attachment_2 = self.env["ir.attachment"].search(
            [("res_id", "=", dfe2.id), ("res_model", "=", "l10n_br_fiscal_dfe.dfe")]
        )
        self.assertTrue(attachment_2)

        result_dfe1 = dfe1.action_download_xml()
        attachment_single_dfe1 = self._get_attachment_from_result(result_dfe1)
        self.assertTrue(attachment_single_dfe1)
        self.assertEqual(attachment_single_dfe1, dfe1.attachment_id)

        result_dfe2_access_key = dfe2.dfe_document_id.action_download_xml()
        attachment_single_dfe2_access_key = self._get_attachment_from_result(
            result_dfe2_access_key
        )
        self.assertTrue(attachment_single_dfe2_access_key)
        with self.assertRaises(UserError):
            dfe1.dfe_document_id.action_download_xml()

    def _get_attachment_from_result(self, result):
        _, _, _, att_id, _ = result["url"].split("/")
        return self.env["ir.attachment"].browse(int(att_id))

    @mock.patch.object(DefaultTransport, "post")
    def test_download_xmls_zip_success(self, _mock_post):
        """Zip download with complete NF-e documents should return a valid zip."""
        _mock_post.return_value = _bytes(response_sucesso_multiplos)
        self.company.dfe_search_documents()

        dfe_docs = self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id)]
        )
        # Filter only documents that have a complete DFe
        docs_with_complete = dfe_docs.filtered(
            lambda d: any(
                r.dfe_nfe_document_type == "dfe_nfe_complete" for r in d.dfe_ids
            )
        )
        self.assertTrue(docs_with_complete)

        result = docs_with_complete.action_download_xmls_zip()

        self.assertEqual(result["type"], "ir.actions.act_url")
        self.assertIn("download=true", result["url"])
        self.assertIn("nfe_xmls.zip", result["url"])

        # Verify zip content
        att_id = int(result["url"].split("/")[3])
        attachment = self.env["ir.attachment"].browse(att_id)
        zip_data = base64.b64decode(attachment.with_context(bin_size=False).datas)
        with zipfile.ZipFile(BytesIO(zip_data), "r") as zf:
            self.assertTrue(zf.namelist(), "Zip should contain at least one file")
            for name in zf.namelist():
                self.assertTrue(name.endswith(".xml"))

    @mock.patch.object(DefaultTransport, "post")
    def test_download_xmls_zip_no_complete(self, _mock_post):
        """Zip download with only summary documents should raise UserError."""
        _mock_post.return_value = _bytes(response_sucesso_multiplos)
        self.company.dfe_search_documents()

        dfe_docs = self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id)]
        )
        # Keep only documents without complete DFe
        docs_summary_only = dfe_docs.filtered(
            lambda d: not any(
                r.dfe_nfe_document_type == "dfe_nfe_complete" for r in d.dfe_ids
            )
        )
        self.assertTrue(docs_summary_only, "Should have at least one summary-only doc")

        with self.assertRaises(UserError):
            docs_summary_only.action_download_xmls_zip()
