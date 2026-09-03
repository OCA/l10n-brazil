# Copyright (C) 2026 - TODAY KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger

WIZARD_LOGGER = "odoo.addons.l10n_br_fiscal.wizards.document_import_wizard"


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

        self.assertIn("not the XML", str(error.exception))
        self.assertIn("DANFE", str(error.exception))

    def test_an_empty_file_is_refused_with_a_readable_message(self):
        with self.assertRaises(UserError) as error:
            self._parse(b"")

        self.assertIn("not the XML", str(error.exception))

    def test_an_xml_of_another_schema_is_refused(self):
        with self.assertRaises(UserError) as error:
            self._parse(b'<invoice xmlns="urn:example"><line/></invoice>')

        self.assertIn("not the XML", str(error.exception))
