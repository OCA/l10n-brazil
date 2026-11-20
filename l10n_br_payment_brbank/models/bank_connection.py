# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from brbank import Capacidade

from odoo import Command, api, models

from odoo.addons.l10n_br_bank_connection.models.connection import (
    adapter_label,
    pix_profile_label,
)

# Settings of the gateways (Asaas, Safrapay) that choose Pix instead of boleto.
PIX_SETTINGS = {"billing_type": "PIX", "meio": "PIX"}


class BankConnection(models.Model):
    _inherit = "l10n_br_bank_connection.connection"

    @api.model_create_multi
    def create(self, vals_list):
        connections = super().create(vals_list)
        connections._brbank_ensure_provider()
        return connections

    def write(self, vals):
        res = super().write(vals)
        if {"adapter", "pix_profile", "company_id"} & set(vals):
            self._brbank_ensure_provider()
        return res

    def _brbank_charges_pix(self):
        """Whether the connection charges by Pix: the Pix BACEN adapter, or a
        gateway whose settings choose Pix."""
        self.ensure_one()
        if self.adapter == "pix_bacen":
            return True
        try:
            settings = json.loads(self.sudo().extra_config or "{}")
        except ValueError:
            return False
        if not isinstance(settings, dict):
            return False
        return any(
            str(settings.get(key) or "").upper() == value
            for key, value in PIX_SETTINGS.items()
        )

    def _brbank_ensure_provider(self):
        """Give each connection a payment provider of its bank.

        A provider already linked to the connection is kept; a provider of the
        same bank without a connection (the records shipped by the module) is
        linked; otherwise a new one is created. It is born disabled and
        unpublished, so nothing reaches the customer until someone enables it.
        """
        Provider = self.env["payment.provider"].sudo()
        for connection in self.filtered("adapter"):
            if connection.adapter == "pix_bacen" and not connection.pix_profile:
                continue
            domain = [
                ("code", "=", "brbank"),
                ("brbank_adapter", "=", connection.adapter),
                ("company_id", "=", connection.company_id.id),
            ]
            if connection.adapter == "pix_bacen":
                domain.append(("brbank_pix_perfil", "=", connection.pix_profile))
            providers = Provider.with_context(active_test=False).search(domain)
            if providers.filtered(lambda p, c=connection: p.brbank_connection_id == c):
                continue
            free = providers.filtered(lambda p: not p.brbank_connection_id)
            if free:
                free[:1].brbank_connection_id = connection
                continue
            pix = connection._brbank_charges_pix()
            if connection.adapter == "pix_bacen":
                bank = f"Pix {pix_profile_label(connection.pix_profile)}"
            else:
                bank = adapter_label(connection.adapter)
            method = self.env.ref(
                "payment.payment_method_pix" if pix else "payment.payment_method_boleto"
            )
            Provider.create(
                {
                    "name": f"{bank} - {connection.name}",
                    "code": "brbank",
                    "brbank_adapter": connection.adapter,
                    "brbank_pix_perfil": connection.pix_profile or False,
                    "brbank_connection_id": connection.id,
                    "company_id": connection.company_id.id,
                    "state": "disabled",
                    "is_published": False,
                    "payment_method_ids": [Command.set(method.ids)],
                }
            )

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
