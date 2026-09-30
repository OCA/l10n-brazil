# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from unittest.mock import patch

from odoo.tests.common import TransactionCase
from odoo.tools import BinaryBytes

WIZARD_MODULE = "odoo.addons.l10n_br_fiscal.wizards.document_import_wizard"


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
