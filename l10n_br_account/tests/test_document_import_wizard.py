# Copyright (C) 2026 - TODAY KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestDocumentImportWizardAttachments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard = cls.env["l10n_br_fiscal.document.import.wizard"]

    def _attachment(self, name, mimetype):
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "mimetype": mimetype,
                "datas": base64.b64encode(b"whatever"),
            }
        )

    def test_a_pdf_alone_is_refused_before_being_parsed(self):
        danfe = self._attachment("Nota Fiscal Eletronica.pdf", "application/pdf")

        with self.assertRaises(UserError) as error:
            self.wizard._get_importer_action(danfe)

        self.assertIn("Nota Fiscal Eletronica.pdf", str(error.exception))

    def test_an_xml_is_recognized_by_its_extension(self):
        attachment = self._attachment("nfe.XML", "application/octet-stream")

        self.assertTrue(self.wizard._is_xml_attachment(attachment))

    def test_an_xml_is_recognized_by_its_mimetype(self):
        attachment = self._attachment("nfe", "text/xml")

        self.assertTrue(self.wizard._is_xml_attachment(attachment))

    def test_a_pdf_is_not_taken_for_an_xml(self):
        attachment = self._attachment("danfe.pdf", "application/pdf")

        self.assertFalse(self.wizard._is_xml_attachment(attachment))

    def test_only_the_xml_attachments_are_linked_to_the_wizard(self):
        """A DANFE uploaded next to the XML must not follow it into the import.

        The selection of a bill often carries the PDF and the XML together, and
        the ones that are not XML are left out of the queue the wizard walks.
        """
        xml = self._attachment("nfe.xml", "application/xml")
        danfe = self._attachment("danfe.pdf", "application/pdf")

        with patch.object(type(self.wizard), "_onchange_file", lambda self: None):
            action = self.wizard._get_importer_action(xml | danfe)

        self.assertEqual(action["res_model"], "l10n_br_fiscal.document.import.wizard")
        self.assertEqual(xml.res_id, action["res_id"])
        self.assertEqual(xml.res_model, "l10n_br_fiscal.document.import.wizard")
        self.assertFalse(danfe.res_id)
