# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from brbank import StatusCanonico, TipoInstrucao
from brbank.erros import Duplicado, Indisponivel

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.l10n_br_payment_brbank.models import payment_transaction

from .common import FAKE, FAKE_BASIC, BrbankTransactionCase

MODULE_LOG = "odoo.addons.l10n_br_payment_brbank.models.boleto_instruction"


@tagged("post_install", "-at_install")
class TestInstructionOnInvoice(BrbankTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider.brbank_rebate_account_id = cls.env["account.account"].create(
            {"name": "Abatimentos", "code": "399001", "account_type": "expense"}
        )
        cls.billing_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Faturista",
                    "login": "faturista_brbank",
                    "email": "faturista@example.com",
                    "company_id": cls.env.company.id,
                    "company_ids": [Command.set(cls.env.company.ids)],
                    "groups_id": [
                        Command.set(
                            cls.env.ref("account.group_account_invoice").ids
                            + cls.env.ref("base.group_user").ids
                        )
                    ],
                }
            )
        )

    def _send(self, tx, **values):
        """Send as an invoicing user, the one the menu is for."""
        instruction = (
            self.env["l10n_br.boleto.instruction"]
            .with_user(self.billing_user)
            .create(dict(values, transaction_id=tx.id))
        )
        return instruction, instruction.action_send()

    def _messages(self, invoice):
        return " ".join(invoice.message_ids.mapped("body"))

    def test_extension_moves_the_installment(self):
        invoice = self._create_invoice()
        txs = self._brbank_txs(invoice)
        first, last = txs[0], txs[2]
        first_date = first.move_line_id.date_maturity
        self._send(last, command="prorrogacao", new_due_date=date(2026, 12, 20))
        self.assertEqual(last.due_date, date(2026, 12, 20))
        self.assertEqual(last.move_line_id.date_maturity, date(2026, 12, 20))
        self.assertEqual(first.move_line_id.date_maturity, first_date)
        self.assertEqual(invoice.invoice_date_due, date(2026, 12, 20))
        self.assertEqual(len(invoice.due_line_ids), 3)
        self.assertIn(last.reference, self._messages(invoice))
        # Core would read the payment term again on the next reconciliation.
        self._set_bank_status(first, StatusCanonico.LIQUIDADO, Decimal("300.00"))
        first._brbank_sync_from_bank()
        self.assertTrue(first.move_line_id.reconciled)
        self.assertEqual(invoice.invoice_date_due, date(2026, 12, 20))
        self.assertEqual(last.move_line_id.date_maturity, date(2026, 12, 20))

    def test_extension_refused_keeps_the_date(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        line_date = tx.move_line_id.date_maturity
        invoice_date = invoice.invoice_date_due
        for command_state, error in (
            ("draft", Indisponivel("fora")),
            ("rejected", None),
        ):
            with self.subTest(state=command_state):
                self.bank["instruction_error"] = error
                self.bank["unsupported"] = (
                    set() if error else {TipoInstrucao.PRORROGACAO}
                )
                instruction, _action = self._send(
                    tx, command="prorrogacao", new_due_date=date(2026, 12, 20)
                )
                self.assertEqual(instruction.state, command_state)
                self.assertEqual(tx.due_date, line_date)
                self.assertEqual(tx.move_line_id.date_maturity, line_date)
                self.assertEqual(invoice.invoice_date_due, invoice_date)

    def test_answer_lost_still_reaches_the_invoice(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        self.bank["instruction_error"] = Duplicado("fake: already applied")
        instruction, _action = self._send(
            tx, command="prorrogacao", new_due_date=date(2026, 12, 20)
        )
        self.assertEqual(instruction.state, "done")
        self.assertEqual(tx.move_line_id.date_maturity, date(2026, 12, 20))

    def test_txid_reaches_the_bank(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        self._send(tx, command="protesto")
        self.assertIn(("txid", tx.txid), self.bank["calls"])

    def test_title_not_confirmed_is_not_live(self):
        self.bank["register_status"] = StatusCanonico.PENDENTE_REGISTRO
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        line = tx.move_line_id
        self.assertEqual(tx.state, "pending")
        self.assertFalse(tx.boleto_pdf)
        self.assertFalse(line.brbank_instruction_available)
        self.assertFalse(invoice._boleto_report_transactions())
        with self.assertRaises(UserError):
            self._send(tx, command="protesto")
        self.assertNotIn(("instrucao", "PROTESTO"), self.bank["calls"])
        invoice.generate_boletos()
        self.assertEqual(len(self._brbank_txs(invoice)), 3)
        self._set_bank_status(tx, StatusCanonico.REGISTRADO)
        tx._brbank_sync_from_bank()
        line.invalidate_recordset()
        self.assertEqual(tx.state, "authorized")
        self.assertTrue(tx.boleto_pdf)
        self.assertTrue(line.brbank_instruction_available)

    def test_customer_without_email_posts(self):
        self.partner.email = False
        invoice = self._create_invoice(post=False)
        invoice.with_user(self.billing_user).action_post()
        txs = self._brbank_txs(invoice)
        self.assertEqual(txs.mapped("state"), ["authorized"] * 3)
        self._send(txs[0], command="baixa")
        self.assertEqual(txs[0].state, "cancel")
        self._set_bank_status(txs[1], StatusCanonico.LIQUIDADO, Decimal("300.00"))
        txs[1].with_user(self.billing_user).action_brbank_check_status()
        self.assertEqual(txs[1].state, "done")
        self.assertTrue(txs[1].move_line_id.reconciled)

    def test_rebate_credit_note(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        line = tx.move_line_id
        self.payment_mode.refund_payment_mode_id = self.payment_mode
        self.partner.customer_payment_mode_id = self.payment_mode
        self._send(tx, command="abatimento", amount=50.0)
        credit_note = line.matched_credit_ids.credit_move_id.move_id
        self.assertEqual(credit_note.move_type, "out_refund")
        self.assertEqual(credit_note.state, "posted")
        self.assertEqual(credit_note.amount_total, 50.0)
        self.assertEqual(credit_note.amount_tax, 0.0)
        self.assertFalse(credit_note.line_ids.tax_ids)
        self.assertEqual(
            credit_note.invoice_line_ids.account_id,
            self.provider.brbank_rebate_account_id,
        )
        # Nothing fiscal, and no boleto charging the credit note.
        self.assertFalse(credit_note.payment_mode_id)
        self.assertFalse(credit_note.transaction_ids)
        for fiscal_field in ("document_type_id", "fiscal_operation_id"):
            if fiscal_field in credit_note._fields:
                self.assertFalse(credit_note[fiscal_field])
        self.assertEqual(credit_note.payment_state, "paid")
        self.assertEqual(line.amount_residual, 250.0)
        self.assertEqual(invoice.amount_residual, 950.0)
        self.assertEqual(tx.amount, 250.0)
        # The customer pays the reduced title: nothing stays open or in credit.
        self._set_bank_status(tx, StatusCanonico.LIQUIDADO, Decimal("250.00"))
        tx._brbank_sync_from_bank()
        self.assertTrue(line.reconciled)
        self.assertEqual(invoice.amount_residual, 700.0)

    def test_rebate_refused_before_the_bank(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        self.bank["calls"].clear()
        account = self.provider.brbank_rebate_account_id
        self.provider.brbank_rebate_account_id = False
        with self.assertRaisesRegex(UserError, "rebate account"):
            self._send(tx, command="abatimento", amount=50.0)
        self.assertFalse(self.bank["calls"])
        self.provider.brbank_rebate_account_id = account

    @mute_logger(MODULE_LOG)
    def test_rebate_local_failure_keeps_the_acceptance(self):
        invoice = self._create_invoice()
        invoice.invoice_user_id = self.billing_user
        tx = self._brbank_txs(invoice)[0]
        with patch.object(
            type(self.env["l10n_br.boleto.instruction"]),
            "_post_rebate_credit_note",
            side_effect=UserError("posting refused"),
        ):
            instruction, action = self._send(tx, command="abatimento", amount=50.0)
        self.assertEqual(instruction.state, "done")
        self.assertIn("posting refused", instruction.result_message)
        self.assertEqual(action["params"]["type"], "danger")
        self.assertEqual(tx.amount, 250.0)
        self.assertEqual(invoice.amount_residual, 1000.0)
        self.assertIn("posting refused", self._messages(invoice))
        activity = invoice.activity_ids
        self.assertEqual(len(activity), 1)
        self.assertIn("posting refused", activity.note)
        self.assertEqual(activity.user_id, self.billing_user)

    def test_entry_offers_what_the_bank_accepts(self):
        invoice = self._create_invoice()
        txs = self._brbank_txs(invoice)
        Instruction = self.env["l10n_br.boleto.instruction"]
        line = txs[0].move_line_id.with_user(self.billing_user)
        self.assertTrue(line.brbank_instruction_available)
        action = line.action_brbank_new_instruction()
        self.assertEqual(action["context"]["default_transaction_id"], txs[0].id)
        self.assertEqual(
            {
                value
                for value, _label in Instruction.with_context(
                    **action["context"]
                ).fields_get(["command"])["command"]["selection"]
            },
            {"prorrogacao", "abatimento", "protesto", "baixa"},
        )
        txs[1].provider_id = self._create_provider(FAKE_BASIC)
        action = txs[1].move_line_id.action_brbank_new_instruction()
        self.assertEqual(
            [
                value
                for value, _label in Instruction.with_context(
                    **action["context"]
                ).fields_get(["command"])["command"]["selection"]
            ],
            ["baixa"],
        )
        # A title that left the bank gets no entry at all.
        txs[2].action_brbank_write_off()
        self.assertFalse(txs[2].move_line_id.brbank_instruction_available)
        with self.assertRaises(UserError):
            txs[2].move_line_id.action_brbank_new_instruction()

    def test_write_off_keeps_the_title_open(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        self._send(tx, command="baixa")
        self.assertEqual(tx.state, "cancel")
        self.assertEqual(invoice.amount_residual, 1000.0)
        self.assertFalse(tx.move_line_id.reconciled)
        self.assertIn("remains open", self._messages(invoice))

    def _with_review_of_write_offs(self):
        self.assertIn("santander", payment_transaction.WRITE_OFF_REVIEW_ADAPTERS)
        return patch.object(payment_transaction, "WRITE_OFF_REVIEW_ADAPTERS", {FAKE})

    def test_write_off_not_commanded_goes_to_review(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        self._set_bank_status(tx, StatusCanonico.BAIXADO)
        with self._with_review_of_write_offs():
            tx._brbank_sync_from_bank()
            tx._brbank_sync_from_bank()
        self.assertEqual(tx.state, "authorized")
        self.assertIn("may have been paid by Pix", tx.brbank_review_message)
        self.assertIn(tx.reference, self._messages(invoice))
        self.assertEqual(len(invoice.activity_ids), 1)

    def test_write_off_commanded_still_cancels(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        with self._with_review_of_write_offs():
            self._send(tx, command="baixa")
        self.assertEqual(tx.state, "cancel")
        self.assertFalse(tx.brbank_review_message)
        self.assertFalse(invoice.activity_ids)
