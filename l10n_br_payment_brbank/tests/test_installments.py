# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import Decimal

from brbank import StatusCanonico
from brbank.erros import Duplicado, Indisponivel, Validacao

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import BrbankTransactionCase


@tagged("post_install", "-at_install")
class TestBrbankInstallments(BrbankTransactionCase):
    def test_one_transaction_per_installment(self):
        invoice = self._create_invoice()
        txs = self._brbank_txs(invoice)
        self.assertEqual(len(txs), 3)
        self.assertEqual(txs.move_line_id, invoice.due_line_ids)
        self.assertEqual(
            txs.mapped("amount"),
            invoice.due_line_ids.sorted("date_maturity").mapped(
                "amount_residual_currency"
            ),
        )
        self.assertEqual(set(txs.mapped("state")), {"authorized"})
        self.assertTrue(all(txs.mapped("provider_reference")))
        self.assertTrue(all(txs.mapped("digitable_line")))
        self.assertTrue(all(txs.mapped("pix_copia_cola")))
        self.assertTrue(all(txs.mapped("txid")))
        self.assertEqual(len(set(txs.mapped("brbank_idempotency_key"))), 3)
        self.assertEqual([call[0] for call in self.bank["calls"]].count("registrar"), 3)

    def test_title_sent_to_the_bank(self):
        invoice = self._create_invoice()
        first = self._brbank_txs(invoice)[0]
        title = self._bank_title(first)
        self.assertEqual(title["valor"], Decimal("300.00"))
        self.assertEqual(title["vencimento"], first.move_line_id.date_maturity)
        self.assertEqual(title["pagador_documento"], "98016373000155")
        titulo = first._brbank_prepare_titulo()
        self.assertEqual(titulo.encargos.multa_percentual, Decimal("2"))
        self.assertEqual(titulo.encargos.juros_mensal_percentual, Decimal("1"))

    def test_generate_again_is_idempotent(self):
        invoice = self._create_invoice()
        invoice.generate_boletos()
        invoice.generate_boletos()
        self.assertEqual(len(self._brbank_txs(invoice)), 3)

    def test_canceled_installment_gets_a_new_title(self):
        invoice = self._create_invoice()
        originals = self._brbank_txs(invoice)
        first = originals[0]
        first.action_brbank_write_off()
        self.assertEqual(first.state, "cancel")
        invoice.generate_boletos()
        new = self._brbank_txs(invoice) - originals
        self.assertEqual(len(new), 1)
        self.assertEqual(new.state, "authorized")
        self.assertEqual(new.move_line_id, first.move_line_id)
        self.assertNotEqual(new.brbank_idempotency_key, first.brbank_idempotency_key)

    def test_second_installment_paid_first(self):
        invoice = self._create_invoice()
        first, second, third = self._brbank_txs(invoice)
        self._set_bank_status(second, StatusCanonico.LIQUIDADO, Decimal("300.00"))
        second._brbank_sync_from_bank()
        self.assertEqual(second.state, "done")
        self.assertTrue(second.payment_id)
        self.assertTrue(second.move_line_id.reconciled)
        self.assertFalse(first.move_line_id.reconciled)
        self.assertFalse(third.move_line_id.reconciled)
        self.assertEqual(first.state, "authorized")
        self.assertAlmostEqual(invoice.amount_residual, 700.0)

    def test_paid_with_interest(self):
        invoice = self._create_invoice()
        first = self._brbank_txs(invoice)[0]
        self._set_bank_status(first, StatusCanonico.LIQUIDADO, Decimal("310.50"))
        first._brbank_sync_from_bank()
        self.assertEqual(first.state, "done")
        self.assertAlmostEqual(first.payment_id.amount, 310.50)
        self.assertTrue(first.move_line_id.reconciled)
        self.assertAlmostEqual(invoice.amount_residual, 700.0)

    def test_bank_unavailable_keeps_the_draft(self):
        self.bank["register_error"] = Indisponivel("banco respondeu HTTP 503")
        invoice = self._create_invoice()
        txs = self._brbank_txs(invoice)
        self.assertEqual(len(txs), 3)
        self.assertEqual(set(txs.mapped("state")), {"draft"})
        self.assertFalse(any(txs.mapped("provider_reference")))
        keys = txs.mapped("brbank_idempotency_key")
        self.bank["register_error"] = None
        self.env["payment.transaction"]._cron_brbank_reconcile()
        self.assertEqual(set(txs.mapped("state")), {"authorized"})
        self.assertEqual(txs.mapped("brbank_idempotency_key"), keys)

    def test_bank_refuses_the_title(self):
        self.bank["register_error"] = Validacao("valor minimo do boleto")
        invoice = self._create_invoice(post=False)
        with self.assertRaisesRegex(UserError, "valor minimo do boleto"):
            invoice.action_post()

    def test_duplicate_reads_the_title_back(self):
        invoice = self._create_invoice(post=False)
        installment = invoice.due_line_ids[:1]
        invoice.action_post()
        tx = self._brbank_txs(invoice).filtered(lambda t: t.move_line_id == installment)
        reference = tx.provider_reference
        tx.write({"provider_reference": False, "state": "draft"})
        self.bank["register_error"] = Duplicado("ja existe", id_banco=reference)
        self.assertTrue(tx._brbank_register())
        self.assertEqual(tx.provider_reference, reference)
        self.assertEqual(tx.state, "authorized")
        self.assertIn(("consultar", reference), self.bank["calls"])

    def test_missing_customer_data_without_personal_data(self):
        self.partner.write({"zip": False})
        with self.assertRaises(UserError) as error:
            self._create_invoice()
        message = str(error.exception)
        # English source or the pt_BR translation, depending on the database.
        self.assertTrue("ZIP code" in message or "CEP" in message, message)
        self.assertNotIn("98016373000155", message)
        self.assertNotIn("11.444.777", message)
        self.assertNotIn("Cliente Boleto", message)
