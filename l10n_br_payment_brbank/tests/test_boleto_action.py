# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from brbank import StatusCanonico, TipoInstrucao
from brbank.erros import Indisponivel, Validacao

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import BrbankTransactionCase, in_days
from .fake_bank import FakeAdapter


@tagged("post_install", "-at_install")
class TestBoletoAction(BrbankTransactionCase):
    def _wizard(self, line, action=None, **values):
        """Open the assistant of the installment and choose `action` (a code)."""
        opened = line.action_brbank_boleto_actions()
        wizard = self.env["l10n_br.boleto.action"].browse(opened["res_id"])
        if action:
            chosen = wizard.available_type_ids.filtered(lambda t: t.code == action)
            self.assertTrue(chosen, f"{action} is not offered")
            values["action_type_id"] = chosen.id
        wizard.write(values)
        return wizard

    def _calls(self, kind):
        return [call for call in self.bank["calls"] if call[0] == kind]

    def _queued(self):
        return self.env["l10n_br.boleto.instruction"].search(
            [("state", "=", "draft"), ("idempotency_key", "!=", False)]
        )

    def _messages(self, invoice):
        return " ".join(invoice.message_ids.mapped("body"))

    # === ASSISTANT === #

    def test_extension_from_the_assistant(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        new_date = in_days(100)
        wizard = self._wizard(
            tx.move_line_id, action="prorrogacao", new_due_date=new_date
        )
        result = wizard.action_confirm()
        self.assertEqual(result["params"]["type"], "success")
        self.assertEqual(
            result["params"]["next"]["type"], "ir.actions.act_window_close"
        )
        instruction = tx.brbank_instruction_ids
        self.assertEqual(instruction.command, "prorrogacao")
        self.assertEqual(instruction.state, "done")
        self.assertEqual(tx.move_line_id.date_maturity, new_date)

    def test_protest_offered_only_when_the_bank_declares_it(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        self.assertIn("protesto", tx._brbank_available_commands())
        declared = frozenset({TipoInstrucao.PRORROGACAO, TipoInstrucao.ABATIMENTO})
        with patch.object(FakeAdapter, "instrucoes", declared, create=True):
            self.assertEqual(
                tx._brbank_available_commands(), ["prorrogacao", "abatimento", "baixa"]
            )

    def test_instructions_follow_the_public_settings(self):
        """The product of the account may narrow the instructions (Bradesco with
        QR code: no protest), read from the public settings only."""
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        seen = []

        # The fake bank has no product setting: numero_cliente plays its part.
        def by_settings(cls, settings):
            seen.append(dict(settings))
            if settings.get("numero_cliente") == 7:
                return frozenset({TipoInstrucao.PRORROGACAO})
            return None

        with patch.object(
            FakeAdapter, "instrucoes_da_config", classmethod(by_settings), create=True
        ):
            self.assertIn("protesto", tx._brbank_available_commands())
            self.provider.brbank_connection_id.extra_config = '{"numero_cliente": 7}'
            self.assertEqual(tx._brbank_available_commands(), ["prorrogacao", "baixa"])
        self.assertEqual(seen[-1], {"numero_cliente": 7})

    # === NEW BOLETO === #

    def test_reissue_without_fees(self):
        invoice = self._create_invoice()
        old = self._brbank_txs(invoice)[0]
        line = old.move_line_id
        old_date = line.date_maturity
        new_date = in_days(10)
        wizard = self._wizard(
            line, action="reemissao", new_due_date=new_date, charge_fees=False
        )
        result = wizard.action_confirm()
        self.assertEqual(result["params"]["type"], "success")
        self.assertEqual(old.state, "cancel")
        self.assertEqual(self._calls("baixar"), [("baixar", old.provider_reference)])
        new = line._brbank_boleto_transaction()
        self.assertNotEqual(new, old)
        self.assertEqual(new.state, "authorized")
        self.assertEqual(new.due_date, new_date)
        self.assertEqual(new.amount, 300.0)
        self.assertTrue(new.brbank_waive_fees)
        fees = new._brbank_prepare_titulo().encargos
        self.assertIsNone(fees.multa_percentual)
        self.assertIsNone(fees.juros_mensal_percentual)
        self.assertEqual(self._bank_title(new)["vencimento"], new_date)
        self.assertEqual(line.date_maturity, new_date)
        self.assertNotEqual(old_date, new_date)
        self.assertIn(new.reference, self._messages(invoice))
        # The portal and the printed invoice show only the new boleto.
        self.assertNotIn(old, invoice._boleto_report_transactions())
        self.assertIn(new, invoice._boleto_report_transactions())

    def test_reissue_keeps_fees_by_default(self):
        invoice = self._create_invoice()
        old = self._brbank_txs(invoice)[0]
        self._wizard(
            old.move_line_id, action="reemissao", new_due_date=in_days(10)
        ).action_confirm()
        new = old.move_line_id._brbank_boleto_transaction()
        self.assertFalse(new.brbank_waive_fees)
        self.assertEqual(new._brbank_prepare_titulo().encargos.multa_percentual, 2)

    def test_reissue_refuses_a_past_date(self):
        invoice = self._create_invoice()
        old = self._brbank_txs(invoice)[0]
        self.bank["calls"].clear()
        wizard = self._wizard(old.move_line_id, action="reemissao")
        # Yesterday at the bank (Brazil), not on the server clock (UTC): between
        # 21:00 and midnight they are different days.
        wizard.new_due_date = wizard._today() - timedelta(days=1)
        with self.assertRaisesRegex(UserError, "today or later"):
            wizard.action_confirm()
        self.assertFalse(self.bank["calls"])

    def test_reissue_stops_when_the_bank_keeps_the_old_boleto(self):
        invoice = self._create_invoice()
        old = self._brbank_txs(invoice)[0]
        line = old.move_line_id
        count = len(invoice.transaction_ids)
        with patch.object(
            FakeAdapter,
            "baixar_titulo",
            new=AsyncMock(side_effect=Validacao("fake: titulo em cartorio")),
        ):
            result = self._wizard(
                line, action="reemissao", new_due_date=in_days(10)
            ).action_confirm()
        self.assertEqual(result["params"]["type"], "danger")
        self.assertIn("cartorio", result["params"]["message"])
        self.assertEqual(old.state, "authorized")
        self.assertEqual(len(invoice.transaction_ids), count)
        self.assertFalse(self._calls("registrar")[3:])

    def test_reissue_waits_when_the_bank_cannot_write_off_yet(self):
        # The BB refuses a write-off in the first 30 minutes after registering.
        invoice = self._create_invoice()
        old = self._brbank_txs(invoice)[0]
        count = len(invoice.transaction_ids)
        with patch.object(
            FakeAdapter,
            "baixar_titulo",
            new=AsyncMock(side_effect=Indisponivel("fake: menos de 30 minutos")),
        ):
            result = self._wizard(
                old.move_line_id, action="reemissao", new_due_date=in_days(10)
            ).action_confirm()
        self.assertEqual(result["params"]["type"], "warning")
        self.assertEqual(old.state, "authorized")
        self.assertEqual(len(invoice.transaction_ids), count)
        # The write-off of an aborted new boleto is never sent later.
        self.assertEqual(old.brbank_instruction_ids.state, "cancel")
        self.assertFalse(self._queued())

    def test_reissue_after_a_write_off(self):
        invoice = self._create_invoice()
        old = self._brbank_txs(invoice)[0]
        old.action_brbank_write_off()
        self.bank["calls"].clear()
        self._wizard(
            old.move_line_id, action="reemissao", new_due_date=in_days(5)
        ).action_confirm()
        self.assertFalse(self._calls("baixar"))
        new = old.move_line_id._brbank_boleto_transaction()
        self.assertEqual(new.state, "authorized")
        # The old transaction no longer offers a second new boleto.
        self.assertFalse(old.brbank_boleto_action_available)
        self.assertTrue(new.brbank_boleto_action_available)

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

    def test_queued_write_off_leaves_the_portal_at_once(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        self.assertIn(tx, invoice._boleto_portal_transactions())
        tx._brbank_queue_write_off("teste")
        self.assertEqual(tx.state, "authorized")
        self.assertNotIn(tx, invoice._boleto_portal_transactions())
        self.assertNotIn(tx, invoice._boleto_report_transactions())

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
