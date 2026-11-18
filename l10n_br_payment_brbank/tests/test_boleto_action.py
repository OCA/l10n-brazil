# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import Decimal
from unittest.mock import AsyncMock, patch

from brbank import StatusCanonico
from brbank.erros import Indisponivel

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import BrbankTransactionCase, in_days
from .fake_bank import FakeAdapter


@tagged("post_install", "-at_install")
class TestBoletoAction(BrbankTransactionCase):
    def _calls(self, kind):
        return [call for call in self.bank["calls"] if call[0] == kind]

    def _queued(self):
        return self.env["l10n_br.boleto.instruction"].search(
            [("state", "=", "draft"), ("idempotency_key", "!=", False)]
        )

    def _messages(self, invoice):
        return " ".join(invoice.message_ids.mapped("body"))

    # === PAST DUE === #

    def test_past_due_boleto_is_not_sent(self):
        invoice = self._create_invoice(post=False)
        invoice.invoice_date = in_days(-100)
        with self.assertRaisesRegex(UserError, "has passed"):
            invoice.action_post()
        self.assertFalse(self._calls("registrar"))

    def test_cron_stops_retrying_a_past_due_boleto(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        late = self.env["payment.transaction"].create(
            dict(
                invoice._brbank_prepare_transaction_values(tx.move_line_id, 1),
                due_date=in_days(-2),
            )
        )
        self.bank["calls"].clear()
        self.env["payment.transaction"]._cron_brbank_reconcile()
        self.assertEqual(late.state, "error")
        self.assertIn("has passed", late.state_message)
        self.assertFalse(self._calls("registrar"))

    # === AUTOMATIC WRITE-OFF === #

    def _pay_in_cash(self, invoice, amount=None):
        journal = self.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", invoice.company_id.id)], limit=1
        )
        # Core proposes the next installment only: pay what the test says.
        values = {"journal_id": journal.id, "amount": amount or invoice.amount_residual}
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create(values).action_create_payments()

    def test_paid_by_other_means_writes_the_boleto_off(self):
        invoice = self._create_invoice()
        txs = self._brbank_txs(invoice)
        self._pay_in_cash(invoice)
        self.assertEqual(invoice.payment_state, "paid")
        queued = self._queued()
        self.assertEqual(queued.transaction_id, txs)
        self.assertEqual(set(queued.mapped("command")), {"baixa"})
        self.assertEqual(txs.mapped("state"), ["authorized"] * 3)
        queued._send_queued()
        self.assertEqual(queued.mapped("state"), ["done"] * 3)
        self.assertEqual(txs.mapped("state"), ["cancel"] * 3)
        self.assertEqual(len(self._calls("baixar")), 3)

    def test_one_installment_paid_writes_off_only_its_boleto(self):
        invoice = self._create_invoice()
        txs = self._brbank_txs(invoice)
        self._pay_in_cash(invoice, amount=300.0)
        self.assertTrue(txs[0].move_line_id.reconciled)
        self.assertEqual(self._queued().transaction_id, txs[0])

    def test_partial_payment_keeps_the_boleto(self):
        invoice = self._create_invoice()
        self._pay_in_cash(invoice, amount=100.0)
        self.assertFalse(self._queued())

    def test_boleto_paid_at_the_bank_is_not_written_off(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        self._set_bank_status(tx, StatusCanonico.LIQUIDADO, Decimal("300.00"))
        tx._brbank_sync_from_bank()
        self.assertTrue(tx.move_line_id.reconciled)
        self.assertFalse(self._queued())

    def test_paid_twice_goes_to_a_person(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        self._pay_in_cash(invoice)
        self._set_bank_status(tx, StatusCanonico.LIQUIDADO, Decimal("300.00"))
        self._queued()._send_queued()
        self.assertEqual(tx.state, "done")
        instruction = tx.brbank_instruction_ids
        self.assertEqual(instruction.state, "cancel")
        self.assertIn("paid twice", self._messages(invoice))
        self.assertNotIn(("baixar", tx.provider_reference), self.bank["calls"])

    def test_unavailable_bank_keeps_the_write_off_queued(self):
        invoice = self._create_invoice()
        self._pay_in_cash(invoice)
        queued = self._queued()
        with patch.object(
            FakeAdapter,
            "baixar_titulo",
            new=AsyncMock(side_effect=Indisponivel("fake: fora do ar")),
        ):
            queued._send_queued()
        self.assertEqual(queued.mapped("state"), ["draft"] * 3)
        self.env["payment.transaction"]._cron_brbank_reconcile()
        self.assertEqual(queued.mapped("state"), ["done"] * 3)

    def test_draft_invoice_writes_its_boletos_off_and_post_issues_new_ones(self):
        invoice = self._create_invoice()
        old = self._brbank_txs(invoice)
        invoice.button_draft()
        self.assertEqual(self._queued().transaction_id, old)
        invoice.action_post()
        live = invoice.transaction_ids.filtered(lambda t: t._brbank_is_live())
        self.assertEqual(len(live), 6)
        self._queued()._send_queued()
        self.assertEqual(old.mapped("state"), ["cancel"] * 3)
        self.assertEqual(
            len(invoice.transaction_ids.filtered(lambda t: t._brbank_is_live())), 3
        )

    def test_canceled_invoice_writes_its_boletos_off(self):
        invoice = self._create_invoice()
        txs = self._brbank_txs(invoice)
        invoice.button_cancel()
        self._queued()._send_queued()
        self.assertEqual(txs.mapped("state"), ["cancel"] * 3)
