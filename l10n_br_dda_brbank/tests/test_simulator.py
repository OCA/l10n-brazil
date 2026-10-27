# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from unittest.mock import patch

from brbank.adapters.btg import BtgAdapter
from brbank.simulador import Simulador
from brbank.simulador.dados import CNPJ_DEMO

from odoo.tests import HttpCase, tagged

from ..utils import source_key
from .common import DdaBrbankCommon

SIMULATED_PAYER = CNPJ_DEMO


@tagged("post_install", "-at_install")
class TestSimulator(HttpCase, DdaBrbankCommon):
    """The real BTG adapter against the bank simulator of the library: HTTP on a
    local port, OAuth included, no mock. `HttpCase` because its test mode lets
    the token store (cursors of its own) share the transaction of the test."""

    def _simulated_connection(self, simulator):
        return self.Connection.create(
            {
                "name": "BTG simulator",
                "adapter": "btg",
                "environment": "test",
                "company_id": self.company.id,
                "cnpj": SIMULATED_PAYER,
                "client_id": "sim-client",
                "client_secret": "sim-secret",
                "refresh_token": "sim-refresh-0",
                "api_base_url_override": simulator.url,
                "token_url_override": f"{simulator.url}/oauth2/token",
                "extra_config": json.dumps(
                    {
                        "agencia": "0001",
                        "conta_corrente": "1234567",
                        "dias_expiracao": 30,
                    }
                ),
            }
        )

    def _count(self, connection):
        debits = self.env["l10n_br_dda.debit"].search(
            [
                ("company_id", "=", self.company.id),
                ("payer_cnpj", "=", SIMULATED_PAYER),
            ]
        )
        sources = self.env["l10n_br_dda.debit.source"].search_count(
            [("source_key", "=", source_key(connection))]
        )
        return debits, sources

    def test_a_full_pull_takes_the_twelve_boletos_and_repeating_does_not_duplicate(
        self,
    ):
        routing = {SIMULATED_PAYER: self.company}
        with Simulador(semente="demo") as simulator, patch.object(
            type(self.Debit), "_dda_company_by_cnpj", lambda model: routing
        ), patch.object(BtgAdapter, "tamanho_pagina_dda", 5):
            connection = self._simulated_connection(simulator)
            # 12 boletos in pages of 5: the cursor of the real adapter at work.
            self.assertEqual(connection._dda_pull(full=True), 12)
            debits, sources = self._count(connection)
            self.assertEqual((len(debits), sources), (12, 12))
            self.assertEqual(connection.state, "connected")
            self.assertTrue(connection.dda_last_full)
            self.assertEqual(connection.dda_sync_status_ids.state, "ok")

            alfa = debits.filtered(lambda d: d.beneficiary_name.startswith("ALFA"))
            self.assertEqual((alfa.amount, alfa.issuer_bank), (1240.0, "341"))
            self.assertEqual(len(alfa.digitable_line), 47)

            self.assertEqual(connection._dda_pull(full=True), 12)
            debits, sources = self._count(connection)
            self.assertEqual((len(debits), sources), (12, 12))

            # The summary of the bank, through the test button.
            connection.write({"dda_enabled": True})
            lines = connection._l10n_br_bank_test_connection()
            self.assertIn("12 boletos", lines[-1])
