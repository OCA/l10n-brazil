# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Nosso numero of the banks whose adapter takes `gerar_nosso_numero`."""

import json
from datetime import date

import httpx

from odoo.exceptions import UserError
from odoo.tests import tagged

from ..models.payment_provider import NOSSO_NUMERO_DIGITS
from .common import BrbankTransactionCase

# Adapters that take `gerar_nosso_numero`, with their digits: the module map follows.
NUMBER_DIGITS = {
    "bb": 10,
    "bradesco": 11,
    "itau": 8,
    "safra": 9,
    "santander": 12,
    "banrisul": 8,
    "caixa": 15,
}
# Reference of an installment with a high id (987654321, attempt 01).
HIGH_REFERENCE = "98765432101"


@tagged("post_install", "-at_install")
class TestNossoNumero(BrbankTransactionCase):
    def setUp(self):
        super().setUp()
        self.sent = []

        def handler(request):
            path = request.url.path
            if "token" in path or path.endswith("/jwt"):
                return httpx.Response(
                    200, json={"access_token": "access-token", "expires_in": 3600}
                )
            self.sent.append(request.content.decode(errors="replace"))
            return httpx.Response(400, json={"message": "refused by the test"})

        self.transport = httpx.MockTransport(handler)

    def _bank_provider(self, adapter):
        provider = self.env.ref(
            f"l10n_br_payment_brbank.payment_provider_brbank_{adapter}"
        )
        self._fill_for_test(provider)
        return provider

    def _bank_tx(self, provider, reference=HIGH_REFERENCE):
        Transaction = self.env["payment.transaction"]
        return Transaction.create(
            {
                "reference": Transaction._compute_reference(
                    "brbank", prefix=f"NN-{provider.brbank_adapter}"
                ),
                "provider_id": provider.id,
                "partner_id": self.partner.id,
                "amount": 50.0,
                "currency_id": self.env.ref("base.BRL").id,
                "operation": "offline",
                "is_boleto_payment": True,
                "due_date": date(2026, 2, 1),
                "brbank_seu_numero": reference,
            }
        )

    def assertNumberSent(self, number, body):
        """The number is in the request, as the bank formats it (zeros on
        the left, agreement or prefix before it, check digits after it)."""
        self.assertIn(number, body)

    def _register(self, tx):
        self.sent.clear()
        tx.with_context(brbank_http_transport=self.transport)._brbank_register(
            raise_on_error=False
        )
        return list(self.sent)

    def test_high_reference_reaches_the_bank(self):
        for adapter in NUMBER_DIGITS:
            with self.subTest(adapter=adapter):
                provider = self._bank_provider(adapter)
                # A number easy to find in the request.
                provider._brbank_nosso_numero_sequence(
                    NUMBER_DIGITS[adapter]
                ).number_next = 4321
                tx = self._bank_tx(provider)
                sent = self._register(tx)
                self.assertTrue(sent, tx.state_message)
                self.assertEqual(tx.brbank_nosso_numero, "4321")
                self.assertNumberSent("4321", sent[0])

    def test_map_follows_the_library(self):
        from brbank import registro

        from odoo.addons.l10n_br_bank_connection.utils import config as brbank_config

        takes_generator = set()
        for name in registro.listar_adapters():
            config_cls = brbank_config.config_class(registro.obter_classe(name))
            keys = {key["name"] for key in brbank_config.describe(config_cls)}
            if "gerar_nosso_numero" in keys:
                takes_generator.add(name)
        self.assertEqual(takes_generator, set(NUMBER_DIGITS))
        self.assertEqual(NOSSO_NUMERO_DIGITS, NUMBER_DIGITS)

    def test_retry_sends_the_same_number(self):
        provider = self._bank_provider("itau")
        provider._brbank_nosso_numero_sequence(8).number_next = 4321
        tx = self._bank_tx(provider)
        first = self._register(tx)
        number = tx.brbank_nosso_numero
        self.assertEqual(number, "4321")
        key = tx.brbank_idempotency_key
        self.assertFalse(tx.provider_reference)
        second = self._register(tx)
        self.assertEqual(tx.brbank_nosso_numero, number)
        self.assertEqual(tx.brbank_idempotency_key, key)
        self.assertNumberSent(number, first[0])
        self.assertNumberSent(number, second[0])
        other = self._bank_tx(provider, reference="98765432102")
        self._register(other)
        self.assertGreater(int(other.brbank_nosso_numero), int(number))

    def test_itau_settings(self):
        provider = self._bank_provider("itau")
        connection = provider.brbank_connection_id
        settings = json.loads(connection.extra_config)
        secrets = json.loads(connection.secret_config)
        settings["bolecode_client_id"] = "credencial-bolecode"
        secrets["bolecode_client_secret"] = "segredo-bolecode"
        secrets["bolecode_certificado_pem"] = "PEM"
        connection.write(
            {"extra_config": json.dumps(settings), "secret_config": json.dumps(secrets)}
        )
        config = provider._brbank_prepare_adapter()[1]
        self.assertEqual(config.bolecode_client_id, "credencial-bolecode")
        self.assertEqual(config.bolecode_client_secret, "segredo-bolecode")
        self.assertEqual(config.bolecode_certificado_pem, b"PEM")
        tx = self._bank_tx(provider)
        tx.write({"provider_reference": "12345678", "state": "authorized"})
        instruction = (
            self.env["l10n_br.boleto.instruction"]
            .with_context(brbank_http_transport=self.transport)
            .create({"transaction_id": tx.id, "command": "protesto"})
        )
        instruction.action_send()
        self.assertEqual(instruction.state, "rejected")
        self.assertIn("dias_protesto", instruction.result_message)

    def test_sequence_skips_numbers_already_sent(self):
        provider = self._bank_provider("bb")
        old = self._bank_tx(provider, reference="4502")
        old.provider_reference = "legacy-title"
        tx = self._bank_tx(provider)
        self._register(tx)
        self.assertEqual(tx.brbank_nosso_numero, "4503")

    def test_sequence_overflow_is_an_error(self):
        provider = self._bank_provider("itau")
        tx = self._bank_tx(provider)
        self._register(tx)
        provider.brbank_nosso_numero_sequence_id.number_next = 10**8
        late = self._bank_tx(provider, reference="98765432102")
        with self.assertRaisesRegex(UserError, "beyond the 8 digits"):
            late.with_context(brbank_http_transport=self.transport)._brbank_register()
        self.assertFalse(late.brbank_nosso_numero)
        self._register(late)
        self.assertEqual(late.state, "error")
        self.assertIn("beyond the 8 digits", late.state_message)
