# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from brbank import Capacidade

from odoo import models


class BankConnection(models.Model):
    _inherit = "l10n_br_bank_connection.connection"

    def _l10n_br_bank_handle_webhook(self, body, headers):
        """Billing side of the webhook: store the events, process them in a cron."""
        counts = super()._l10n_br_bank_handle_webhook(body, headers)
        adapter_class = self._l10n_br_bank_adapter_class()
        if adapter_class is None or Capacidade.WEBHOOK not in adapter_class.capacidades:
            return counts
        # Parsing is local work: it must not flip the state of the connection.
        events = self._l10n_br_bank_run(
            lambda adapter: adapter.parse_webhook(body, headers), record=False
        )
        created = self.env["l10n_br.brbank.event"].sudo()._brbank_store(self, events)
        if created:
            self.env.ref(
                "l10n_br_payment_brbank.ir_cron_brbank_process_events"
            ).sudo()._trigger()
        counts["received"] = counts.get("received", 0) + len(events)
        counts["new"] = counts.get("new", 0) + len(created)
        return counts
