# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.tests import tagged

from odoo.addons.l10n_br_dda.tests.common import PAYER_2

from .common import DdaBrbankCommon, make_debit, make_event


@tagged("post_install", "-at_install")
class TestWebhook(DdaBrbankCommon):
    def test_events_are_stored_and_the_cron_is_triggered(self):
        event = make_event("e-1", self.NEW, make_debit(1))
        counts, trigger = self.webhook(event)
        self.assertEqual((counts["dda"], counts["dda_new"]), (1, 1))
        trigger.assert_called_once()
        stored = self.event_of("e-1")
        self.assertEqual(stored.state, "new")
        self.assertEqual(stored.event_type, "DEBITO_NOVO")
        # The boleto waits in the event as values of the inbox.
        vals = json.loads(stored.debits_json)
        self.assertEqual(vals[0]["digitable_line"], make_debit(1).linha_digitavel)
        self.assertEqual(vals[0]["status"], "ABERTO")
        self.assertEqual(vals[0]["external_id"], "bank-1")
        self.assertFalse(self.debits_of(), "nothing is processed in the request")

    def test_a_resent_event_is_not_stored_nor_triggered_again(self):
        event = make_event("e-1", self.NEW, make_debit(1))
        self.webhook(event)
        counts, trigger = self.webhook(event)
        self.assertEqual((counts["dda"], counts["dda_new"]), (1, 0))
        trigger.assert_not_called()
        self.assertEqual(len(self.Event.search([("event_id", "=", "e-1")])), 1)

    def test_state_toggles_without_bank_id_are_all_kept(self):
        disabled = make_event("h-off", self.DISABLED, cnpj_pagador=None)
        enabled = make_event("h-on", self.ENABLED, cnpj_pagador=None)
        for event in (disabled, enabled, disabled):
            counts, _trigger = self.webhook(event)
            self.assertEqual(counts["dda_new"], 1)
        stored = self.Event.search(
            [("connection_id", "=", self.connection.id)], order="id"
        )
        self.assertEqual(stored.mapped("event_id"), ["h-off", "h-on", "h-off#1"])
        self.assertEqual(stored[-1].event_type, self.DISABLED.value)

    def test_a_notification_without_dda_events_is_not_an_error(self):
        counts, trigger = self.webhook()
        self.assertEqual((counts["dda"], counts["dda_new"]), (0, 0))
        trigger.assert_not_called()
        self.assertFalse(
            self.Event.search([("connection_id", "=", self.connection.id)])
        )

    def test_events_of_another_payer_are_not_stored(self):
        stranger = make_event(
            "e-x", self.NEW, make_debit(2, cnpj_pagador=PAYER_2), cnpj_pagador=PAYER_2
        )
        mixed = make_event(
            "e-y", self.NEW, make_debit(3), make_debit(4, cnpj_pagador=PAYER_2)
        )
        counts, _trigger = self.webhook(stranger, mixed)
        self.assertEqual(counts["dda_new"], 1)
        self.assertFalse(self.event_of("e-x"))
        # In the event that is kept, only the boleto of the connection stays.
        vals = json.loads(self.event_of("e-y").debits_json)
        self.assertEqual([v["external_id"] for v in vals], ["bank-3"])
