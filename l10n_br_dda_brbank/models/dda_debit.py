# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models

from ..utils import source_key

ADMIN_GROUP = "l10n_br_bank_connection.group_bank_connection_admin"
CONNECTION_MODEL = "l10n_br_bank_connection.connection"


class DdaDebit(models.Model):
    _inherit = "l10n_br_dda.debit"

    @api.model
    def _dda_source_status(self):
        """Add the bank connections that have DDA turned on (or that failed)."""
        sources = super()._dda_source_status()
        can_open = self.env.user.has_group(ADMIN_GROUP)
        # Stays on the panel while its DDA status is an error.
        failed = (
            self.env["l10n_br_bank_connection.sync_status"]
            .sudo()
            .search([("domain", "=", "dda"), ("state", "=", "error")])
            .connection_id
        )
        connections = (
            self.env[CONNECTION_MODEL]
            .sudo()
            .search(
                [
                    "|",
                    ("dda_enabled", "=", True),
                    ("id", "in", failed.ids),
                    ("company_id", "in", self.env.companies.ids),
                ]
            )
        )
        for connection in connections:
            status = connection.dda_sync_status_ids[:1]
            if connection.state in ("error", "needs_reconsent"):
                state = "error"
                message = connection.last_error or _("The connection needs attention.")
            elif status:
                state, message = status.state, status.message or ""
            else:
                state, message = "warning", _("No synchronization yet.")
            action = False
            if can_open:
                action = {
                    "type": "ir.actions.act_window",
                    "res_model": CONNECTION_MODEL,
                    "res_id": connection.id,
                    "views": [[False, "form"]],
                    "target": "current",
                }
            sources.append(
                {
                    "key": source_key(connection),
                    "name": connection.name,
                    "state": state,
                    "last_sync": status.last_date if status else False,
                    "message": message,
                    "action": action,
                }
            )
        return sources
