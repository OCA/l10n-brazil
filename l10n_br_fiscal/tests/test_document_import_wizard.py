# Copyright (C) 2026 - TODAY KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tools import BinaryBytes, mute_logger

WIZARD_MODULE = "odoo.addons.l10n_br_fiscal.wizards.document_import_wizard"
WIZARD_LOGGER = WIZARD_MODULE


class TestDocumentImportWizardFile(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard = cls.env["l10n_br_fiscal.document.import.wizard"]

    def _parse(self, content):
        with mute_logger(WIZARD_LOGGER):
            return self.wizard._parse_file_data(base64.b64encode(content))

    def test_a_pdf_is_refused_with_a_readable_message(self):
        pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n%%EOF\n"

        with self.assertRaises(UserError) as error:
            self._parse(pdf)

        self.assertIn("Could not read this file", str(error.exception))
        self.assertIn("printed representation (PDF)", str(error.exception))
        self.assertNotIn("DANFE", str(error.exception))

    def test_an_empty_file_is_refused_with_a_readable_message(self):
        with self.assertRaises(UserError) as error:
            self._parse(b"")

        self.assertIn("Could not read this file", str(error.exception))

    def test_an_xml_of_another_schema_is_refused(self):
        with self.assertRaises(UserError) as error:
            self._parse(b'<invoice xmlns="urn:example"><line/></invoice>')

        self.assertIn("Could not read this file", str(error.exception))


class TestDocumentImportWizardOperationType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "Emitente Teste", "vat": "53939351000129"}
        )

    def _operation_type(self, issuer_cnpj):
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].new(
            {"company_id": self.company.id, "issuer_cnpj": issuer_cnpj}
        )
        return wizard.fiscal_operation_type

    def test_own_document_is_outgoing_whatever_the_cnpj_format(self):
        """The access key gives a formatted CNPJ; the company vat is not."""
        self.assertEqual(self._operation_type("53.939.351/0001-29"), "out")
        self.assertEqual(self._operation_type("53939351000129"), "out")

    def test_third_party_document_is_incoming(self):
        self.assertEqual(self._operation_type("12.345.678/0001-95"), "in")


class TestDocumentImportWizard(TransactionCase):
    def test_parse_file_data(self):
        """The XML reaches the parser as raw bytes.

        Since 20.0 a Binary field is read as a BinaryValue holding the raw
        content (base64 is only used on the wire), while callers may still
        pass a base64 encoded value.
        """
        xml = b"<nfeProc/>"
        wizard_model = self.env["l10n_br_fiscal.document.import.wizard"]
        with patch(f"{WIZARD_MODULE}.XmlParser", create=True) as parser:
            parser.return_value.from_bytes.side_effect = lambda data: data
            self.assertEqual(wizard_model._parse_file_data(BinaryBytes(xml)), xml)
            self.assertEqual(wizard_model._parse_file_data(base64.b64encode(xml)), xml)
