# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from brbank import Capacidade, StatusCanonico, TipoInstrucao
from brbank.erros import Indisponivel, Validacao
from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import FAKE_BASIC, BrbankTransactionCase
from .fake_bank import FakeAdapter


@tagged("post_install", "-at_install")
class TestBrbankTransaction(BrbankTransactionCase):
    def _standalone_tx(self):
        tx = self.env["payment.transaction"].create(
            {
                "reference": self.env["payment.transaction"]._compute_reference(
                    "brbank", prefix="TESTE"
                ),
                "provider_id": self.provider.id,
                "partner_id": self.partner.id,
                "amount": 50.0,
                "currency_id": self.env.ref("base.BRL").id,
                "operation": "offline",
                "is_boleto_payment": True,
                "due_date": date(2026, 2, 1),
            }
        )
        tx._brbank_register()
        return tx

    def test_state_map(self):
        expected = {
            StatusCanonico.PENDENTE_REGISTRO: "pending",
            StatusCanonico.REGISTRADO: "authorized",
            StatusCanonico.BAIXADO: "cancel",
            StatusCanonico.REJEITADO: "error",
        }
        for status, state in expected.items():
            with self.subTest(status=status):
                tx = self._standalone_tx()
                tx.state = "draft"
                tx._brbank_apply_status(status)
                self.assertEqual(tx.state, state)

    def test_state_map_settled(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        tx._brbank_apply_status(StatusCanonico.LIQUIDADO)
        self.assertEqual(tx.state, "done")
        self.assertTrue(tx.payment_id)
        self.assertTrue(tx.is_post_processed)

    def test_done_never_goes_back(self):
        invoice = self._create_invoice()
        tx = self._brbank_txs(invoice)[0]
        tx._brbank_apply_status(StatusCanonico.LIQUIDADO)
        payment = tx.payment_id
        tx._brbank_apply_status(StatusCanonico.BAIXADO)
        self.assertEqual(tx.state, "done")
        self.assertEqual(payment.state, "posted")

    def test_capture_reads_the_bank(self):
        tx = self._standalone_tx()
        self._set_bank_status(tx, StatusCanonico.LIQUIDADO, Decimal("50.00"))
        tx.action_capture()
        self.assertEqual(tx.state, "done")

    def test_instruction_supported(self):
        tx = self._standalone_tx()
        instruction = self.env["l10n_br.boleto.instruction"].create(
            {
                "transaction_id": tx.id,
                "command": "prorrogacao",
                "new_due_date": date(2026, 3, 1),
            }
        )
        self.assertTrue(instruction.action_send())
        self.assertEqual(instruction.state, "done")
        self.assertTrue(instruction.idempotency_key)
        self.assertEqual(tx.due_date, date(2026, 3, 1))
        self.assertEqual(self._bank_title(tx)["vencimento"], date(2026, 3, 1))
        self.assertIn(("instrucao", "PRORROGACAO"), self.bank["calls"])

    def test_instruction_not_supported_by_the_bank(self):
        tx = self._standalone_tx()
        self.bank["unsupported"] = {TipoInstrucao.PROTESTO}
        instruction = self.env["l10n_br.boleto.instruction"].create(
            {"transaction_id": tx.id, "command": "protesto"}
        )
        action = instruction.action_send()
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(instruction.state, "rejected")
        self.assertIn("not supported", instruction.result_message)
        self.assertEqual(tx.state, "authorized")

    def test_instruction_capability_missing(self):
        provider = self._create_provider(FAKE_BASIC)
        self.assertFalse(provider.brbank_supports_instruction)
        self.assertTrue(provider.brbank_supports_write_off)
        tx = self._standalone_tx()
        tx.provider_id = provider
        instruction = self.env["l10n_br.boleto.instruction"].create(
            {"transaction_id": tx.id, "command": "protesto"}
        )
        with self.assertRaises(UserError):
            instruction.action_send()
        self.assertNotIn(("instrucao", "PROTESTO"), self.bank["calls"])

    def test_write_off(self):
        tx = self._standalone_tx()
        tx.action_brbank_write_off()
        self.assertEqual(tx.state, "cancel")
        self.assertEqual(tx.brbank_bank_status, "BAIXADO")

    def test_pdf_downloaded_when_the_bank_provides_it(self):
        tx = self._standalone_tx()
        self.assertTrue(tx.boleto_pdf)
        action = tx.action_brbank_download_pdf()
        self.assertIn(f"/web/content/payment.transaction/{tx.id}/", action["url"])

    def test_pdf_drawn_when_the_bank_has_none(self):
        tx = self._standalone_tx()
        self.env.company.partner_id.cnpj_cpf = "91.300.766/0001-47"
        # Boleto of R$ 15,00 from the Banco do Brasil test set: a valid barcode.
        tx.write(
            {
                "amount": 15.0,
                "boleto_pdf": False,
                "digitable_line": False,
                "barcode": "00195313800000015000000003051284190526000117",
            }
        )
        with patch.object(FakeAdapter, "capacidades", Capacidade.BAIXA):
            tx.provider_id.invalidate_recordset(["brbank_supports_pdf"])
            tx.invalidate_recordset(["brbank_supports_pdf"])
            self.assertTrue(tx._brbank_fetch_pdf())
        self.assertTrue(base64.b64decode(tx.boleto_pdf).startswith(b"%PDF"))

    def test_invalid_bank_code_explains_why_there_is_no_pdf(self):
        tx = self._standalone_tx()
        tx.write(
            {
                "boleto_pdf": False,
                "digitable_line": False,
                "barcode": "00195313800000015000000003051284190526000118",
            }
        )
        with patch.object(FakeAdapter, "capacidades", Capacidade.BAIXA):
            tx.provider_id.invalidate_recordset(["brbank_supports_pdf"])
            tx.invalidate_recordset(["brbank_supports_pdf"])
            self.assertFalse(tx._brbank_fetch_pdf())
            with self.assertRaisesRegex(UserError, "valid boleto"):
                tx.action_brbank_download_pdf()

    def test_core_capture_and_void_hidden_on_boletos(self):
        invoice = self._create_invoice()
        self.assertTrue(invoice.authorized_transaction_ids)
        self.assertTrue(invoice.brbank_hide_capture)
        conditions = {
            ("account.move", "payment_action_capture"): "brbank_hide_capture",
            ("account.move", "payment_action_void"): "brbank_hide_capture",
            ("payment.transaction", "action_capture"): "provider_code",
            ("payment.transaction", "action_void"): "provider_code",
        }
        for (model, button), condition in conditions.items():
            with self.subTest(button=button):
                arch = etree.fromstring(
                    self.env[model].get_views([(False, "form")])["views"]["form"][
                        "arch"
                    ]
                )
                node = arch.xpath(f"//button[@name='{button}']")[0]
                self.assertIn(condition, node.get("modifiers"))

    def test_print_boletos_of_the_invoice(self):
        invoice = self._create_invoice()
        self.assertTrue(invoice.brbank_boleto_printable)
        action = invoice.action_brbank_print_boletos()
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "account.move"), ("res_id", "=", invoice.id)]
        )
        self.assertEqual(len(attachment), 1)
        self.assertIn(f"/web/content/{attachment.id}", action["url"])
        self.assertTrue(base64.b64decode(attachment.datas).startswith(b"%PDF"))
        invoice.action_brbank_print_boletos()
        self.assertEqual(
            self.env["ir.attachment"].search_count(
                [("res_model", "=", "account.move"), ("res_id", "=", invoice.id)]
            ),
            1,
        )

    def test_reconcile_cron(self):
        invoice = self._create_invoice()
        txs = self._brbank_txs(invoice)
        self._set_bank_status(txs[0], StatusCanonico.LIQUIDADO, Decimal("300.00"))
        self._set_bank_status(txs[1], StatusCanonico.BAIXADO)
        self.bank["calls"].clear()
        self.env.ref(
            "l10n_br_payment_brbank.ir_cron_brbank_reconcile"
        ).method_direct_trigger()
        self.assertEqual(txs.mapped("state"), ["done", "cancel", "authorized"])
        consulted = {call[1] for call in self.bank["calls"] if call[0] == "consultar"}
        self.assertTrue(set(txs.mapped("provider_reference")) <= consulted)

    def test_cron_fills_the_synchronization_tab(self):
        self._create_invoice()
        cron = self.env.ref("l10n_br_payment_brbank.ir_cron_brbank_reconcile")
        connection = self.provider.brbank_connection_id

        def status():
            return connection.sync_status_ids.filtered(
                lambda s: s.domain == "collection"
            )

        cron.method_direct_trigger()
        self.assertEqual(status().state, "ok")
        self.assertTrue(status().last_date)
        cases = (
            (Validacao("fake: titulo inexistente"), "error"),
            (Indisponivel("fake: fora do ar"), "warning"),
        )
        for error, state in cases:
            with self.subTest(state=state), patch.object(
                FakeAdapter, "consultar_titulo", new=AsyncMock(side_effect=error)
            ):
                cron.method_direct_trigger()
                self.assertEqual(status().state, state)
                self.assertIn(str(error), status().message)

    def test_report_shows_the_titles(self):
        invoice = self._create_invoice()
        html = (
            self.env["ir.actions.report"]
            ._render_qweb_html("account.account_invoices", invoice.ids)[0]
            .decode()
        )
        for tx in self._brbank_txs(invoice):
            self.assertIn(tx.digitable_line, html)
            self.assertIn(tx.pix_copia_cola, html)

    def test_cnab_bridge(self):
        tx = self._standalone_tx()
        self._set_bank_status(tx, StatusCanonico.LIQUIDADO, Decimal("50.00"))
        found = self.env["payment.transaction"]._brbank_notify_cnab_occurrence(
            tx.our_number
        )
        self.assertEqual(found, tx)
        self.assertEqual(tx.state, "done")
