# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import json
import time
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from brbank import registro
from brbank.erros import Indisponivel
from brbank.pagamento import (
    LoteRegistrado,
    PagamentoRegistrado,
    StatusLote,
    StatusPagamento,
    TipoPagamento,
)

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.auth_totp.models.totp import hotp
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT
from odoo.addons.l10n_br_payment_schedule.tests.test_payment_schedule_br import brcode

# Test data of the Banco do Brasil homologation environment.
BOLETO = "00195313800000015000000003051284190526000117"
GUIA = "83630000000641400052836100812355200812351310"
# Fictitious CNPJs (valid check digits, not in the Federal Revenue registry).
SUPPLIER_CNPJ = "98.016.373/0001-55"
COMPANY_CNPJ = "91300766000147"
OTHER_CNPJ = "84526081000158"
LOG_BATCH = "odoo.addons.account_payment_order_api.models.account_payment_api_batch"
LOG_BRBANK = "odoo.addons.l10n_br_account_payment_order_brbank.models"
WIZARD = "odoo.addons.account_payment_order_api.wizard"
SECRET = b"12345678901234567890"
CREDENTIALS = {"client_id": "client-id", "client_secret": "client-secret"}


def token_answer(request):
    if "token" in request.url.path or "jwt" in request.url.path:
        return httpx.Response(
            200,
            json={"access_token": "token", "expires_in": 3600, "token_type": "bearer"},
        )
    return None


def refusing_bank(requests, request):
    requests.append(request)
    if "proximos-numeros" in request.url.path:
        return httpx.Response(200, json={"listaProximosNumeros": [26545]})
    return token_answer(request) or httpx.Response(400, json={})


@dataclass
class FakeConfig:
    conta: str


class FakeBank:
    """What the fake adapter sends and answers, shared with the test."""

    def __init__(self):
        self.sent = []
        self.authorized = []
        self.send_error = None
        self.batch_queries = 0
        self.line_status = {}
        self.payment_status = StatusPagamento.PAGO
        self.batch_status = StatusLote.ACEITO


class FakeAdapter:
    """Payment adapter double, with the capabilities of the real class."""

    bank = None
    banco = "fake"
    capacidades_pagamento = None

    def __init__(self, config: FakeConfig, *, client=None):
        self.config = config

    async def aclose(self):
        return None

    async def reservar_numero_lote(self):
        return "26545"

    async def pagar_lote(self, lote):
        self.bank.sent.append(lote)
        if self.bank.send_error:
            raise self.bank.send_error
        return self._registered(lote.numero, lote.tipo, lote.pagamentos)

    async def consultar_lote(self, id_banco, tipo):
        self.bank.batch_queries += 1
        registered = self._registered(id_banco, tipo, self.bank.sent[-1].pagamentos)
        return registered.model_copy(
            update={
                "status": self.bank.batch_status,
                "pagamentos": tuple(
                    p.model_copy(update={"chave_idempotencia": None})
                    for p in registered.pagamentos
                ),
            }
        )

    async def consultar_pagamento(self, id_banco, tipo):
        return PagamentoRegistrado(
            banco=self.banco,
            id_banco=id_banco,
            status=self.bank.payment_status,
            valor=Decimal("15.00"),
            autenticacao="A0329DB0",
        )

    async def autorizar_lote(self, lote, conta_debito):
        self.bank.authorized.append((lote, conta_debito))
        return lote.model_copy(
            update={
                "pagamentos": tuple(
                    p.model_copy(update={"status": StatusPagamento.EM_PROCESSAMENTO})
                    for p in lote.pagamentos
                )
            }
        )

    def _registered(self, numero, tipo, pagamentos):
        statuses = self.bank.line_status
        return LoteRegistrado(
            banco=self.banco,
            id_banco=numero,
            tipo=tipo,
            status=StatusLote.ACEITO,
            pagamentos=tuple(
                PagamentoRegistrado(
                    banco=self.banco,
                    id_banco=statuses[i][1] if i in statuses else f"900265457310{i}",
                    status=statuses[i][0] if i in statuses else StatusPagamento.ACEITO,
                    chave_idempotencia=p.chave_idempotencia,
                    motivos=statuses[i][2] if i in statuses else (),
                )
                for i, p in enumerate(pagamentos)
            ),
        )


@tagged("-at_install", "post_install")
class TestBrbankProvider(AccountTestInvoicingCommon):
    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, lang="en_US", **DISABLED_MAIL_CONTEXT)
        )
        cls.company = cls.company_data["company"]
        cls.company.partner_id.vat = COMPANY_CNPJ
        # The bills are only the source of the payable items: the core l10n_br makes
        # a Brazilian purchase journal ask for a fiscal document type.
        purchase_journal = cls.company_data["default_journal_purchase"]
        if "l10n_latam_use_documents" in purchase_journal._fields:
            purchase_journal.l10n_latam_use_documents = False
        bank_bb = cls.env["res.bank"].create(
            {"name": "Banco do Brasil", "code_bc": "001", "ispb_number": "00000000"}
        )
        cls.journal = cls.company_data["default_journal_bank"]
        cls.journal.bank_account_id = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.company.partner_id.id,
                "bank_id": bank_bb.id,
                "bra_number": "1607",
                "acc_number": "99738672",
                "acc_number_dig": "1",
            }
        )
        cls.supplier = cls.env["res.partner"].create(
            {"name": "Fornecedor Teste", "is_company": True, "vat": SUPPLIER_CNPJ}
        )
        cls.supplier_bank = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.supplier.id,
                "bank_id": bank_bb.id,
                "bra_number": "551",
                "acc_number": "60840",
                "acc_number_dig": "8",
            }
        )
        cls.pix_key = cls.env["res.partner.pix"].create(
            {
                "partner_id": cls.supplier.id,
                "key_type": "email",
                "key": "pix@example.com",
            }
        )

    def setUp(self):
        super().setUp()
        self.registry.enter_test_mode(self.cr)
        self.addCleanup(self.registry.leave_test_mode)
        self.bank = FakeBank()

    def _use_fake(self):
        real = registro.obter_classe_pagamento

        def fake(name):
            return type(
                "Fake",
                (FakeAdapter,),
                {
                    "bank": self.bank,
                    "banco": name,
                    "capacidades_pagamento": real(name).capacidades_pagamento,
                },
            )

        patcher = patch.object(registro, "obter_classe_pagamento", fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _mode(self, adapter="bb", domain=False, contract="731030", **connection_values):
        connection = self.env["l10n_br_bank_connection.connection"].create(
            {
                "name": adapter,
                "adapter": adapter,
                "environment": "test",
                **CREDENTIALS,
                **connection_values,
            }
        )
        return self.env["account.payment.mode"].create(
            {
                "name": f"API {adapter}",
                "company_id": self.company.id,
                "bank_account_link": "fixed",
                "fixed_journal_id": self.journal.id,
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_out"
                ).id,
                "payment_mode_domain": domain,
                "api_provider": "brbank",
                "bank_connection_id": connection.id,
                "brbank_contract": contract,
            }
        )

    def _order(self, mode, lines=1, pay_today_in=None, **line_values):
        order = self.env["account.payment.order"].create(
            {"payment_mode_id": mode.id, "payment_type": "outbound"}
        )
        for _index in range(lines):
            bill = self.init_invoice(
                "in_invoice", amounts=[15.0], post=True, partner=self.supplier
            )
            bill.line_ids.filtered(
                lambda x: x.account_id.account_type == "liability_payable"
            ).create_payment_line_from_move_line(order)
        order.payment_line_ids.write(dict({"communication": "NF 1"}, **line_values))
        if pay_today_in:
            order.date_prefered = "now"
        order.with_context(tz=pay_today_in or self.env.context.get("tz")).draft2open()
        return order

    # Kinds -------------------------------------------------------------------

    def test_batch_kind_by_line(self):
        self._use_fake()
        batch_model = self.env["account.payment.api.batch"]
        cases = [
            ("bb", {"barcode": BOLETO}, "BOLETO"),
            ("bb", {"barcode": GUIA}, "GUIA"),
            ("bb", {"partner_pix_id": self.pix_key.id}, "PIX"),
            (
                "bb",
                {"partner_bank_id": self.supplier_bank.id, "partner_pix_id": False},
                "TRANSFERENCIA",
            ),
            ("sicoob", {"pix_copy_paste": brcode(key=OTHER_CNPJ)}, "PIX_QRCODE"),
        ]
        for adapter, values, kind in cases:
            payline = self._order(self._mode(adapter), **values).payment_line_ids
            self.assertEqual(batch_model._api_batch_key("brbank", payline), kind)

    def test_kind_not_declared_fails_before_the_bank(self):
        self._use_fake()
        code = brcode(key=OTHER_CNPJ)
        for adapter, values in (
            ("itau", {"barcode": BOLETO}),
            ("bradesco", {"pix_copy_paste": code}),
            ("bb", {"pix_copy_paste": code}),
            ("sicoob", {"barcode": GUIA}),
            (
                "inter",
                {"partner_bank_id": self.supplier_bank.id, "partner_pix_id": False},
            ),
        ):
            order = self._order(self._mode(adapter), **values)
            with self.assertRaisesRegex(UserError, "Nothing was sent"):
                order._api_send_to_bank()
            self.assertFalse(order.api_batch_ids)
        self.assertFalse(self.bank.sent)

    def test_static_qr_with_other_amount_stops_without_payment_data(self):
        self._use_fake()
        code = brcode(key=OTHER_CNPJ, amount="99.00")
        order = self._order(self._mode("sicoob"), pix_copy_paste=code)
        with self.assertRaises(UserError) as caught:
            order._api_send_to_bank()
        self.assertIn("valor diferente", str(caught.exception))
        self.assertNotIn(code, str(caught.exception))
        self.assertFalse(self.bank.sent)

    def test_qr_line_goes_with_the_code(self):
        self._use_fake()
        code = brcode(key=OTHER_CNPJ)
        order = self._order(self._mode("itau"), pix_copy_paste=code)
        order._api_send_to_bank()
        (lote,) = self.bank.sent
        self.assertIs(lote.tipo, TipoPagamento.PIX_QRCODE)
        self.assertEqual(lote.pagamentos[0].brcode, code)
        self.assertEqual(order.api_line_ids.state, "awaiting_release")

    def test_ted_carries_the_partner_name(self):
        self._use_fake()
        order = self._order(
            self._mode("bradesco"),
            partner_bank_id=self.supplier_bank.id,
            partner_pix_id=False,
        )
        order._api_send_to_bank()
        self.assertEqual(
            self.bank.sent[0].pagamentos[0].favorecido_nome, "Fornecedor Teste"
        )

    # Batch at the bank --------------------------------------------------------

    def test_send_boleto_waits_for_release(self):
        self._use_fake()
        order = self._order(self._mode(), barcode=BOLETO)
        order._api_send_to_bank()
        (lote,) = self.bank.sent
        self.assertEqual(lote.numero, "26545")
        self.assertEqual(lote.conta_debito.agencia, "1607")
        (payment,) = lote.pagamentos
        self.assertEqual(payment.codigo_barras, BOLETO)
        self.assertEqual(payment.beneficiario_documento, "98016373000155")
        line = order.api_line_ids
        self.assertEqual(line.state, "awaiting_release")

        self.env["account.payment.api.batch"]._cron_api_check()
        self.assertEqual(line.state, "paid")
        self.assertEqual(line.authentication, "A0329DB0")
        self.assertIn(line.payment_id.state, ("in_process", "paid"))
        self.assertEqual(order.state, "uploaded")

    def test_unknown_outcome_recovered_by_batch_query(self):
        self._use_fake()
        self.bank.send_error = Indisponivel("timeout")
        order = self._order(self._mode(), partner_pix_id=self.pix_key.id)
        order._api_send_to_bank()
        self.assertEqual(order.api_batch_ids.state, "uncertain")
        self.bank.send_error = None
        order.action_api_check()
        self.assertEqual(order.api_batch_ids.state, "sent")
        self.assertEqual(order.api_line_ids.state, "awaiting_release")
        self.assertEqual(len(self.bank.sent), 1)

    def test_released_batch_shows_processing(self):
        self._use_fake()
        order = self._order(self._mode(), barcode=BOLETO)
        order._api_send_to_bank()
        self.bank.batch_status = StatusLote.EM_PROCESSAMENTO
        self.bank.payment_status = StatusPagamento.ACEITO
        order.action_api_check()
        self.assertEqual(order.api_line_ids.state, "processing")
        self.assertEqual(order.api_line_ids.payment_id.state, "draft")

    # Local batch --------------------------------------------------------------

    def test_local_batch_unknown_and_not_sent(self):
        """Paid now, no answer on the second, third not sent; only the query runs."""
        self._use_fake()
        self.bank.line_status = {
            0: (StatusPagamento.PAGO, "E1", ()),
            1: (StatusPagamento.INDETERMINADO, "E2", ("SEM_RESPOSTA",)),
            2: (StatusPagamento.RECUSADO, "", ("NAO_ENVIADO",)),
        }
        order = self._order(
            self._mode("sicoob"), lines=3, partner_pix_id=self.pix_key.id
        )
        order._api_send_to_bank()
        paid, unknown, not_sent = order.api_line_ids.sorted("id")
        self.assertEqual(paid.state, "paid")
        self.assertEqual(paid.payment_id.state, "in_process")
        self.assertEqual(unknown.state, "unknown")
        self.assertEqual(unknown.payment_id.state, "draft")
        self.assertEqual(not_sent.state, "refused")
        self.assertEqual(not_sent.payment_id.state, "canceled")
        self.assertIn("new payment order", not_sent.reason)
        self.assertFalse(order.api_can_send)
        self.assertEqual(order.state, "open")

        self.bank.payment_status = StatusPagamento.EM_PROCESSAMENTO
        order.action_api_check()
        self.assertEqual(self.bank.batch_queries, 0)
        self.assertEqual(unknown.state, "processing")
        self.bank.payment_status = StatusPagamento.PAGO
        order.action_api_check()
        self.assertEqual(unknown.state, "paid")
        self.assertEqual(order.state, "uploaded")
        self.assertEqual(len(self.bank.sent), 1)

    def test_local_batch_unknown_without_id_stays_for_manual_check(self):
        self._use_fake()
        self.bank.line_status = {
            0: (StatusPagamento.INDETERMINADO, "", ("SEM_RESPOSTA",))
        }
        order = self._order(
            self._mode("bradesco"),
            partner_bank_id=self.supplier_bank.id,
            partner_pix_id=False,
        )
        order._api_send_to_bank()
        line = order.api_line_ids
        self.assertEqual(line.state, "unknown")
        self.assertIn("bank statement", line.reason)
        order.action_api_check()
        self.assertEqual(line.state, "unknown")
        self.assertEqual(self.bank.batch_queries, 0)
        self.assertFalse(line.payment_id.state == "canceled")

    def test_cancel_not_declared_says_so(self):
        self._use_fake()
        order = self._order(self._mode("itau"), partner_pix_id=self.pix_key.id)
        order._api_send_to_bank()
        with self.assertRaisesRegex(UserError, "bank channel"):
            order.api_line_ids.action_api_cancel()

    # Authorization --------------------------------------------------------------

    def _manager(self):
        return new_test_user(
            self.env,
            login="payment-manager",
            groups="account.group_account_manager,"
            "account_payment_order.group_account_payment",
            company_id=self.company.id,
        )

    def _session_of(self, user):
        """A user with the authenticator on, in a session of the wizard."""
        user.sudo().totp_secret = base64.b32encode(SECRET).decode()
        return patch(
            f"{WIZARD}.account_payment_api_second_factor.request",
            SimpleNamespace(session=SimpleNamespace(uid=user.id)),
        )

    def test_authorize_rebuilds_the_batch_and_logs(self):
        self._use_fake()
        order = self._order(self._mode("santander"), partner_pix_id=self.pix_key.id)
        self.assertFalse(order.brbank_can_authorize)
        order._api_send_to_bank()
        line = order.api_line_ids
        self.assertEqual(line.state, "awaiting_release")
        self.assertTrue(order.brbank_can_authorize)

        user = new_test_user(
            self.env, login="payment-clerk", groups="account.group_account_invoice"
        )
        with self.assertRaises(AccessError):
            order.with_user(user).action_brbank_authorize()

        manager = self._manager()
        with self._session_of(manager):
            action = order.with_user(manager).action_brbank_authorize()
            self.assertEqual(action["res_model"], "account.payment.api.second.factor")
            self.assertFalse(self.bank.authorized, "no money before the code")
            wizard = self.env[action["res_model"]].with_user(manager)
            wizard = wizard.browse(action["res_id"])
            wizard.code = str(hotp(SECRET, int(time.time() / 30))).zfill(6)
            self.env.flush_all()
            wizard.action_confirm()
        ((registered, account),) = self.bank.authorized
        self.assertEqual(registered.id_banco, "26545")
        self.assertIs(registered.tipo, TipoPagamento.PIX)
        (payment,) = registered.pagamentos
        self.assertEqual(payment.id_banco, line.bank_reference)
        self.assertEqual(payment.chave_idempotencia, str(line.id))
        self.assertEqual(payment.valor, Decimal(str(line.amount)))
        self.assertEqual(account.agencia, "1607")
        self.assertEqual(line.state, "processing")
        self.assertFalse(order.brbank_can_authorize)
        messages = order.message_ids.filtered(lambda m: "authorized" in (m.body or ""))
        self.assertEqual(messages.author_id, manager.partner_id)
        self.assertIn(manager.name, messages.body)
        with self.assertRaisesRegex(UserError, "nothing to authorize"):
            order.action_brbank_authorize()

    def test_second_factor_by_bank(self):
        for adapter, forced in (
            ("bradesco", True),
            ("sicoob", True),
            ("inter", True),
            ("santander", True),
            ("bb", False),
            ("itau", False),
        ):
            mode = self._mode(adapter)
            self.assertEqual(mode.api_require_second_factor, forced, adapter)
            if forced:
                with self.assertRaisesRegex(ValidationError, "second factor"):
                    mode.api_require_second_factor = False
            else:
                mode.api_require_second_factor = True
                self.assertTrue(mode.api_require_second_factor)

    def test_send_without_bank_approval_asks_for_the_code(self):
        self._use_fake()
        order = self._order(self._mode("bradesco"), partner_pix_id=self.pix_key.id)
        with self._session_of(self.env.user):
            action = order.action_api_send()
        self.assertEqual(action["res_model"], "account.payment.api.second.factor")
        self.assertFalse(self.bank.sent)

    def test_authorize_is_only_for_the_bank_that_needs_it(self):
        self._use_fake()
        order = self._order(self._mode(), partner_pix_id=self.pix_key.id)
        order._api_send_to_bank()
        self.assertFalse(order.brbank_can_authorize)
        with self.assertRaisesRegex(UserError, "nothing to authorize"):
            order.action_brbank_authorize()

    # Payment schedule ---------------------------------------------------------

    def _schedule_item(self, mode):
        bill = self.init_invoice(
            "in_invoice", amounts=[15.0], partner=self.supplier, post=False
        )
        bill.payment_mode_id = mode
        bill.action_post()
        return bill.line_ids.filtered(
            lambda line: line.account_type == "liability_payable"
        )

    def test_schedule_copy_and_paste_is_an_instrument(self):
        self._use_fake()
        self.supplier.pix_key_ids.unlink()
        qr_mode = self._mode("sicoob", domain="pix_transfer")
        no_qr_mode = self._mode("bradesco", domain="pix_transfer")
        code = brcode(url="pix.example.com/qr/v2/abc")
        item = self._schedule_item(qr_mode)
        no_qr = self._schedule_item(no_qr_mode)
        mismatch = self._schedule_item(qr_mode)
        item.payment_pix_copy_paste = code
        no_qr.payment_pix_copy_paste = code
        mismatch.payment_pix_copy_paste = brcode(key=OTHER_CNPJ)
        states = {item: "to_schedule", no_qr: "missing_instrument"}
        states[mismatch] = "missing_instrument"
        for line, state in states.items():
            self.assertEqual(line.payment_schedule_state, state)
            found = self.env["account.move.line"].search(
                [("id", "=", line.id), ("payment_schedule_state", "=", state)]
            )
            self.assertEqual(found, line, f"search and compute disagree on {state}")

        order = item._payment_schedule_create_orders()
        payline = order.payment_line_ids
        self.assertEqual(payline.pix_copy_paste, code)
        payline.communication = "NF 1"
        order.draft2open()
        order._api_send_to_bank()
        self.assertEqual(self.bank.sent[0].pagamentos[0].brcode, code)

    # Real adapters ---------------------------------------------------------------

    def test_real_adapters_config_and_first_request(self):
        """Each real class, built from the Odoo data, up to its first request."""
        cases = {
            "bb": ("/proximos-numeros-requisicao", "gw-dev-app-key=dev-key", {}),
            "sicoob": ("/pix-pagamentos/v2/pagamentos", "client_id", {}),
            "inter": ("/banking/v2/pix", "x-id-idempotente", {}),
            "santander": (
                "/workspaces/ws-1/pix_payments",
                "x-application-key",
                {"workspace_id": "ws-1"},
            ),
            "itau": ("/transferencias", "x-itau-apikey", {}),
            "bradesco": ("/v1/spi/solicitar-transferencia", "authorization", {}),
        }
        for adapter, (path, marker, settings) in cases.items():
            with self.subTest(adapter=adapter):
                requests = []
                secrets = {"chave_desenvolvedor": "dev-key"} if adapter == "bb" else {}
                mode = self._mode(
                    adapter,
                    brbank_payment_settings=json.dumps(settings),
                    secret_config=json.dumps(secrets),
                )
                order = self._order(
                    mode,
                    partner_pix_id=self.pix_key.id,
                    pay_today_in="America/Sao_Paulo"
                    if adapter == "bradesco"
                    else "UTC",
                )
                transport = httpx.MockTransport(partial(refusing_bank, requests))
                with mute_logger(LOG_BATCH):
                    order.with_context(
                        brbank_http_transport=transport
                    )._api_send_to_bank()
                calls = [
                    r
                    for r in requests
                    if "token" not in r.url.path and "jwt" not in r.url.path
                ]
                self.assertTrue(calls, "no request reached the bank")
                self.assertTrue(str(calls[0].url.path).endswith(path), calls[0].url)
                self.assertIn(
                    marker, f"{calls[0].url.query.decode()} {dict(calls[0].headers)}"
                )

    def _santander_authorized(self, patch_answer):
        """Send through the real Santander adapter, then authorize at it."""
        patches = []

        def bank(request):
            token = token_answer(request)
            if token:
                return token
            if request.method == "POST":
                body = json.loads(request.content)
                return httpx.Response(
                    201, json={"id": body["id"], "status": "READY_TO_PAY"}
                )
            patches.append(json.loads(request.content))
            return patch_answer(request)

        mode = self._mode(
            "santander",
            brbank_payment_settings=json.dumps({"workspace_id": "ws-1"}),
        )
        order = self._order(mode, partner_pix_id=self.pix_key.id, pay_today_in="UTC")
        order = order.with_context(brbank_http_transport=httpx.MockTransport(bank))
        order._api_send_to_bank()
        line = order.api_line_ids
        self.assertEqual(line.state, "awaiting_release")
        self.assertFalse(patches, "the send step must not authorize")
        order.with_user(self._manager())._brbank_authorize_confirmed()
        return order, line, patches

    def test_santander_real_adapter_moves_money_only_on_authorize(self):
        order, line, patches = self._santander_authorized(
            lambda request: httpx.Response(
                200,
                json={
                    "id": "x",
                    "status": "PAYED",
                    "transaction": {"code": "AUT1", "value": "15.00"},
                },
            )
        )
        (body,) = patches
        self.assertEqual(body["status"], "AUTHORIZED")
        self.assertEqual(body["debitAccount"]["number"], "000997386721")
        self.assertEqual(line.state, "paid")
        self.assertEqual(order.state, "uploaded")

    def test_santander_real_adapter_authorize_without_answer_is_not_repeated(self):
        order, line, patches = self._santander_authorized(
            lambda request: httpx.Response(500, json={})
        )
        self.assertEqual(len(patches), 1)
        self.assertEqual(line.state, "unknown")
        self.assertTrue(line.bank_reference)
        self.assertFalse(order.brbank_can_authorize)

    def test_config_of_each_bank(self):
        cnpj = COMPANY_CNPJ
        self.company.legal_name = "Empresa Ficticia Ltda"
        cases = {
            "bb": ({"contrato": "731030", "tipo_pagamento": 126}, {}),
            "sicoob": (
                {"pagador_documento": cnpj, "pagador_nome": "Empresa Ficticia Ltda"},
                {},
            ),
            "inter": ({"conta_corrente": None}, {}),
            "santander": (
                {"workspace_id": "ws-1", "pagador_documento": cnpj},
                {"brbank_payment_settings": json.dumps({"workspace_id": "ws-1"})},
            ),
            "itau": ({"documento_pagador": cnpj}, {}),
            "bradesco": (
                {
                    "agencia": "1607",
                    "conta_corrente": "99738672",
                    "digito_conta": "1",
                    "pagador_nome": "Empresa Ficticia Ltda",
                    "pix_client_id": "pix-client",
                },
                {
                    "brbank_payment_settings": json.dumps(
                        {"pix_client_id": "pix-client"}
                    )
                },
            ),
        }
        for adapter, (expected, values) in cases.items():
            secrets = {"chave_desenvolvedor": "dev-key"} if adapter == "bb" else {}
            mode = self._mode(adapter, secret_config=json.dumps(secrets), **values)
            connection = mode.bank_connection_id
            config = connection._l10n_br_bank_payment_config(
                connection._l10n_br_bank_payment_adapter_class(), mode
            )
            self.assertEqual(config.ambiente, "sandbox")
            for key, value in expected.items():
                self.assertEqual(getattr(config, key), value, f"{adapter} {key}")

    def test_missing_config_says_which_key_and_no_secret(self):
        mode = self._mode("santander", client_secret="very-secret-value")
        connection = mode.bank_connection_id
        with self.assertRaises(UserError) as caught:
            connection._l10n_br_bank_payment_config(
                connection._l10n_br_bank_payment_adapter_class(), mode
            )
        self.assertIn("workspace_id", str(caught.exception))
        self.assertNotIn("very-secret-value", str(caught.exception))

    def test_adapter_without_payment_class(self):
        with self.assertRaisesRegex(UserError, "cannot send payments"):
            self._mode("caixa", environment="prod")
