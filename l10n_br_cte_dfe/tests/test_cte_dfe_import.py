# Copyright 2026 Engenere.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import zipfile
from io import BytesIO
from unittest import mock

from xsdata.formats.dataclass.transports import DefaultTransport

from odoo.tests.common import TransactionCase

from .common import CTE_ACCESS_KEY, response_cte_only


class TestCteDfeImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.cte_dfe_next_query = False
        # l10n_br_cte demo/tests may leave a fiscal document with this key
        cls.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", CTE_ACCESS_KEY)]
        ).unlink()

    def _fetch_document(self, mock_post):
        mock_post.return_value = response_cte_only()
        self.company.cte_dfe_search_documents()
        return self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id), ("fiscal_type", "=", "cte")]
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_import_cte(self, mock_post):
        document = self._fetch_document(mock_post)
        self.assertFalse(document.fiscal_document_id)

        # the generic import of the inbox reads the complete DF-e XML with the reader
        # of l10n_br_cte
        # the web client reads the sizes of the binary fields (bin_size): the XML
        # is read as content all the same
        action = document.with_context(bin_size=True).import_document()
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        fiscal_document = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", CTE_ACCESS_KEY)], limit=1
        )
        self.assertEqual(action["res_id"], fiscal_document.id)
        self.assertEqual(fiscal_document.document_type_id.code, "57")
        # the CT-e of the fixture is issued by a company of the database: the reader
        # imports it as a document of that company, an output
        self.assertEqual(fiscal_document.fiscal_operation_type, "out")
        self.assertEqual(fiscal_document.issuer, "company")
        self.assertTrue(fiscal_document.imported_document)
        # non-stored compute read before the import: drop the cached value
        document.invalidate_recordset(["fiscal_document_id"])
        self.assertEqual(document.fiscal_document_id, fiscal_document)

        action = document.action_view_imported_document()
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        self.assertEqual(action["res_id"], fiscal_document.id)

    @mock.patch.object(DefaultTransport, "post")
    def test_generate_dacte(self, mock_post):
        document = self._fetch_document(mock_post)

        result = document.make_pdf()

        self.assertEqual(result["type"], "ir.actions.act_url")
        self.assertIn("download=true", result["url"])
        attachment_id = int(result["url"].split("/")[3].split("?")[0])
        attachment = self.env["ir.attachment"].browse(attachment_id)
        self.assertEqual(attachment.name, f"DACTE_{CTE_ACCESS_KEY}.pdf")
        pdf = base64.b64decode(attachment.with_context(bin_size=False).datas)
        self.assertTrue(pdf.startswith(b"%PDF"))

    @mock.patch.object(DefaultTransport, "post")
    def test_download_xml_and_zip(self, mock_post):
        document = self._fetch_document(mock_post)

        result = document.action_download_xml()
        self.assertIn(f"procCTe_{CTE_ACCESS_KEY}.xml", result["url"])

        result = document.action_download_xmls_zip()
        attachment = self.env["ir.attachment"].browse(int(result["url"].split("/")[3]))
        zip_data = base64.b64decode(attachment.with_context(bin_size=False).datas)
        with zipfile.ZipFile(BytesIO(zip_data)) as zf:
            self.assertEqual(zf.namelist(), [f"procCTe_{CTE_ACCESS_KEY}.xml"])
            self.assertIn(b"<cteProc", zf.read(zf.namelist()[0]))
