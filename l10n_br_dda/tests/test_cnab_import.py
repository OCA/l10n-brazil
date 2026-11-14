# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import date

from odoo.exceptions import UserError
from odoo.tools.misc import file_path

from .common import PAYER, DdaCommon

FILE_PAYER = "91300766000147"


class TestCnabImport(DdaCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.structure = cls.env.ref(
            "l10n_br_dda.cnab_structure_dda_simulated", raise_if_not_found=False
        )
        path = file_path("l10n_br_dda/tests/data/dda_return_simulated.rem")
        with open(path, encoding="utf-8") as handle:
            cls.content = handle.read().replace(FILE_PAYER, PAYER)
        cls.vendor = cls.make_vendor("Import Vendor One", "779065020001")

    def _wizard(self, content=None):
        if not self.structure:
            self.skipTest("The simulated structure comes with the demo data.")
        return self.env["l10n_br_dda.import.wizard"].create(
            {
                "cnab_structure_id": self.structure.id,
                "return_file": base64.b64encode((content or self.content).encode()),
                "filename": "dda_return_simulated.rem",
            }
        )

    def test_structure_is_marked_as_dda_and_simulated(self):
        if not self.structure:
            self.skipTest("The simulated structure comes with the demo data.")
        self.assertTrue(self.structure.is_dda_return)
        self.assertIn("simulated", self.structure.name)

    def test_import_creates_boletos_from_the_structure(self):
        action = self._wizard().action_import()
        debits = self.env["l10n_br_dda.debit"].search(action["domain"])
        self.assertEqual(len(debits), 4)
        by_line = {d.digitable_line[-1]: d for d in debits}
        first = by_line["1"]
        self.assertEqual(first.amount, 1234.56)
        self.assertEqual(first.date_due, date(2026, 12, 15))
        self.assertEqual(first.document_number, "9001/1")
        self.assertEqual(first.partner_id, self.vendor)
        self.assertEqual(first.company_id, self.company)
        self.assertEqual(first.source_ids.source_type, "cnab")
        self.assertTrue(first.source_ids.source_key.startswith("cnab:"))
        self.assertEqual(by_line["3"].state, "cancelled")
        self.assertEqual(by_line["4"].state, "paid_elsewhere")
        self.assertEqual(by_line["4"].amount, 2000.0)

    def test_reimporting_the_file_changes_nothing(self):
        self._wizard().action_import()
        count = self.env["l10n_br_dda.debit"].search_count([])
        self._wizard().action_import()
        self.assertEqual(self.env["l10n_br_dda.debit"].search_count([]), count)
        debit = self.env["l10n_br_dda.debit"].search(
            [("document_number", "=", "9002")], limit=1
        )
        self.assertEqual(len(debit.source_ids), 1)

    def test_file_of_another_bank_is_refused(self):
        wrong = "\n".join("999" + line[3:] for line in self.content.splitlines())
        with self.assertRaises(UserError):
            self._wizard(wrong).action_import()

    def test_cnab_source_status(self):
        if not self.structure:
            self.skipTest("The simulated structure comes with the demo data.")
        before = self.env["l10n_br_dda.debit"]._dda_source_status()
        self.assertEqual(before[0]["key"], "cnab")
        self.assertIn(before[0]["state"], ("ok", "warning"))
        self._wizard().action_import()
        after = self.env["l10n_br_dda.debit"]._dda_source_status()
        self.assertEqual(after[0]["state"], "ok")
        self.assertTrue(after[0]["last_sync"])
        self.assertTrue(after[0]["action"])
