# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A bank connection brings its payment provider."""

import json

from odoo.tests import tagged

from .common import BrbankTransactionCase


@tagged("post_install", "-at_install")
class TestConnectionProvider(BrbankTransactionCase):
    def _connection(self, adapter, settings=None, **values):
        """A connection not yet connected: its settings may be incomplete."""
        values.setdefault("state", "draft")
        values["extra_config"] = json.dumps(settings or {})
        return self._create_connection(adapter, **values)

    def _providers(self, connection):
        return (
            self.env["payment.provider"]
            .with_context(active_test=False)
            .search([("brbank_connection_id", "=", connection.id)])
        )

    def test_links_the_provider_shipped_without_a_connection(self):
        shipped = self.env.ref("l10n_br_payment_brbank.payment_provider_brbank_safra")
        shipped.brbank_connection_id = False
        connection = self._connection("safra")
        self.assertEqual(self._providers(connection), shipped)
        self.assertEqual(shipped.state, "disabled")

    def test_second_account_gets_a_new_disabled_provider(self):
        first = self._connection("safra", name="Conta 1")
        second = self._connection("safra", name="Conta 2")
        provider = self._providers(second)
        self.assertEqual(len(provider), 1)
        self.assertNotEqual(provider, self._providers(first))
        self.assertEqual(provider.state, "disabled")
        self.assertFalse(provider.is_published)
        self.assertEqual(provider.name, "Safra (422) - Conta 2")
        self.assertEqual(
            provider.payment_method_ids, self.env.ref("payment.payment_method_boleto")
        )

    def test_gateway_without_shipped_provider_and_pix_setting(self):
        boleto = self._connection("safrapay", name="Loja")
        provider = self._providers(boleto)
        self.assertEqual(provider.brbank_adapter, "safrapay")
        self.assertIn("Safrapay", provider.name)
        pix = self._connection("safrapay", {"meio": "PIX"}, name="Loja Pix")
        self.assertEqual(
            self._providers(pix).payment_method_ids,
            self.env.ref("payment.payment_method_pix"),
        )

    def test_pix_needs_the_profile(self):
        connection = self._connection("pix_bacen")
        self.assertFalse(self._providers(connection))
        connection.pix_profile = "inter"
        provider = self._providers(connection)
        self.assertEqual(provider.brbank_pix_perfil, "inter")
        self.assertEqual(
            provider.payment_method_ids, self.env.ref("payment.payment_method_pix")
        )

    def test_existing_link_is_kept(self):
        connection = self._connection("safra")
        provider = self._providers(connection)
        connection.write({"name": "Renomeada"})
        connection.write({"company_id": connection.company_id.id})
        self.assertEqual(self._providers(connection), provider)
