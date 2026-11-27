# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged

SUPPLIER_KEY = "35261173623891000106550010000041011062777168"
OWN_KEY = "35261081583054000129550010000090011760018051"
DUE_TYPES = ("asset_receivable", "liability_payable")


@tagged("post_install", "-at_install")
class TestDemoInvoices(TransactionCase):
    """The notes imported by the demo of l10n_br_nfe come with their invoices."""

    def _document(self, key):
        document = self.env["l10n_br_fiscal.document"].search(
            [("document_key", "=", key)]
        )
        if not document:
            self.skipTest("the demo data is not installed")
        return document

    def _due_lines(self, move):
        return move.line_ids.filtered(
            lambda line: line.account_id.account_type in DUE_TYPES
        ).sorted("date_maturity")

    def test_the_note_of_the_supplier_has_its_bill_posted(self):
        document = self._document(SUPPLIER_KEY)

        (move,) = document.move_ids

        self.assertEqual((move.move_type, move.state), ("in_invoice", "posted"))
        due = self._due_lines(move)
        self.assertEqual(
            [line.date_maturity.isoformat() for line in due],
            ["2026-12-10", "2027-01-10"],
        )
        self.assertEqual(due.mapped("credit"), [70.0, 70.0])

    def test_the_own_note_has_its_customer_invoice_posted(self):
        document = self._document(OWN_KEY)

        (move,) = document.move_ids

        self.assertEqual((move.move_type, move.state), ("out_invoice", "posted"))
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertEqual(document.authorization_protocol, "135260000000901")
