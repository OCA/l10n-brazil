# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import AccountEdiCase


@tagged("post_install", "-at_install")
class TestGenerateInvoice(AccountEdiCase):
    def _generate(self, document):
        action = document.action_generate_invoice()
        self.assertEqual(action["res_model"], "account.move")
        return self.env["account.move"].browse(action["res_id"])

    def test_no_payable_exists_before_the_invoice_is_generated(self):
        before = self._payables()
        with self._declared((self._day(3, 10), 400.0), (self._day(4, 10), 600.0)):
            document = self._imported_document()

            self.assertEqual(self._payables(), before)
            self.assertFalse(document.move_ids)

            move = self._generate(document)

        self.assertEqual(self._payables() - before, self._due_lines(move))
        self.assertEqual(len(self._due_lines(move)), 2)

    def test_due_lines_follow_the_declared_installments(self):
        with self._declared((self._day(3, 10), 400.0), (self._day(4, 10), 600.0)):
            move = self._generate(self._imported_document())

        due_lines = self._due_lines(move)
        self.assertEqual(
            due_lines.mapped("date_maturity"), [self._day(3, 10), self._day(4, 10)]
        )
        self.assertEqual(due_lines.mapped("credit"), [400.0, 600.0])
        self.assertAlmostEqual(sum(move.line_ids.mapped("balance")), 0.0, places=2)

    def test_installments_that_do_not_add_up_are_spread_by_their_weight(self):
        # declared 300.00 against a net amount payable of 1000.00
        with self._declared(
            (self._day(3, 10), 100.0),
            (self._day(4, 10), 100.0),
            (self._day(5, 10), 100.0),
        ):
            document = self._imported_document()
            warning = document._edi_installment_warning()
            move = self._generate(document)

        self.assertIn("300.00", warning)
        self.assertIn("1000.00", warning)
        # the residue of the rounding goes to the last installment
        amounts = [round(line.credit, 2) for line in self._due_lines(move)]
        self.assertEqual(amounts, [333.33, 333.33, 333.34])
        self.assertAlmostEqual(sum(amounts), 1000.0, places=2)

    def test_installments_are_spread_by_weight_not_equally(self):
        with self._declared((self._day(3, 10), 100.0), (self._day(4, 10), 300.0)):
            move = self._generate(self._imported_document())

        self.assertEqual(self._due_lines(move).mapped("credit"), [250.0, 750.0])

    def test_withholding_is_discounted_from_the_declared_installments(self):
        with self._declared((self._day(3, 10), 500.0), (self._day(4, 10), 500.0)):
            move = self._generate(
                self._imported_document(
                    issqn_wh_tax_id=self.env.ref("l10n_br_fiscal.tax_issqn_wh_5").id,
                    issqn_wh_base=1000.0,
                    issqn_wh_percent=5.0,
                    issqn_wh_value=50.0,
                )
            )

        self.assertEqual(self._due_lines(move).mapped("credit"), [475.0, 475.0])

    def test_payment_term_applies_when_no_installment_is_declared(self):
        self.supplier.property_supplier_payment_term_id = self.payment_term
        with self._declared():
            move = self._generate(self._imported_document())

        self.assertEqual(move.invoice_payment_term_id, self.payment_term)
        due_lines = self._due_lines(move)
        self.assertEqual(len(due_lines), 2)
        self.assertEqual(due_lines.mapped("credit"), [500.0, 500.0])

    def test_total_of_the_invoice_is_the_total_declared_by_the_counterparty(self):
        # 10 CX at 35.00 converted to 120 UN: 120 x 2.92 would give 350.40
        document = self._imported_document(
            quantity=120.0, price_unit=2.92, partner_price_gross=350.0
        )
        self.assertAlmostEqual(document.amount_financial_total, 350.0, places=2)
        with self._declared():
            move = self._generate(document)

        self.assertAlmostEqual(move.amount_total, 350.0, places=2)
        self.assertAlmostEqual(move.invoice_line_ids.price_subtotal, 350.0, places=2)
        self.assertAlmostEqual(sum(move.line_ids.mapped("debit")), 350.0, places=2)
        self.assertAlmostEqual(
            sum(self._due_lines(move).mapped("credit")), 350.0, places=2
        )

    def test_line_not_resolved_refuses_the_invoice(self):
        document = self._imported_document(import_state="pending")

        with self.assertRaisesRegex(UserError, "Resolve the lines"):
            document.action_generate_invoice()
        self.assertFalse(document.move_ids)

    def test_user_without_accounting_rights_gets_a_clear_message(self):
        user = self.env["res.users"].create(
            {
                "name": "Fiscal only",
                "email": "fiscal-only@example.com",
                "login": "edi_fiscal_no_billing",
                "groups_id": [
                    Command.set(
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("l10n_br_fiscal.group_user").id,
                        ]
                    )
                ],
            }
        )
        document = self._imported_document()

        with self.assertRaisesRegex(UserError, "accounting rights"):
            document.with_user(user).action_generate_invoice()

    def test_upload_to_a_vendor_bill_opens_the_imported_document(self):
        document = self._imported_document()
        attachment = self.env["ir.attachment"].create(
            {"name": "nfe.xml", "raw": b"<nfe/>"}
        )
        journal = self.company_data["default_journal_purchase"]
        model = type(self.env["l10n_br_fiscal.document"])

        with mock.patch.object(
            model, "_edi_import_files", return_value=(document, [], [])
        ) as imported:
            action = journal.create_document_from_attachment([attachment.id])

        imported.assert_called_once()
        self.assertEqual(imported.call_args.args[0], [("nfe.xml", b"<nfe/>")])
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        self.assertEqual(action["res_id"], document.id)

    def test_upload_without_a_brazilian_company_keeps_the_standard_flow(self):
        attachment = self.env["ir.attachment"].create(
            {"name": "bill.pdf", "raw": b"%PDF"}
        )
        journal = self.company_data["default_journal_purchase"]
        self.company.country_id = self.env.ref("base.us")
        model = type(self.env["l10n_br_fiscal.document"])

        with mock.patch.object(model, "_edi_import_files") as imported:
            action = journal.create_document_from_attachment([attachment.id])

        imported.assert_not_called()
        self.assertEqual(action["res_model"], "account.move")

    def test_a_document_without_amount_to_pay_gets_no_invoice(self):
        """The type of the document can say that it is only registered: the button
        goes away and the action refuses, with the reason."""
        reason = "Registered only, with no amount to pay."
        with self._declared((self._day(3, 10), 400.0), (self._day(4, 10), 600.0)):
            document = self._imported_document()
            self.assertTrue(document.edi_can_generate_invoice)
            document_model = type(document)
            with mock.patch.object(
                document_model, "_edi_no_payable_reason", lambda doc: reason
            ):
                document.invalidate_recordset(["edi_can_generate_invoice"])
                self.assertFalse(document.edi_can_generate_invoice)
                with self.assertRaises(UserError) as error:
                    document.action_generate_invoice()
                self.assertEqual(error.exception.args[0], reason)
                self.assertFalse(document.move_ids)
            document.invalidate_recordset(["edi_can_generate_invoice"])
            self.assertTrue(document.edi_can_generate_invoice)
