# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import EdiImportCase


class TestDocumentLineLot(EdiImportCase):
    def test_a_line_declares_no_lot_unless_its_type_reads_them(self):
        document = self._create_imported_document(lines=[{}, {}])

        for line in document.fiscal_line_ids:
            self.assertEqual(line._edi_get_lots(), [])
