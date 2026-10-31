# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .connection import STATE_COLORS


class BankConnectionSyncStatus(models.Model):
    """Last synchronization of a domain on a connection."""

    _name = "l10n_br_bank_connection.sync_status"
    _description = "Bank Connection Synchronization Status"
    _order = "connection_id, domain"
    _rec_name = "domain"

    connection_id = fields.Many2one(
        comodel_name="l10n_br_bank_connection.connection",
        required=True,
        ondelete="cascade",
        index=True,
    )
    domain = fields.Selection(
        selection=[("collection", "Billing"), ("dda", "DDA")],
        required=True,
    )
    last_date = fields.Datetime()
    state = fields.Selection(
        selection=[("ok", "OK"), ("warning", "Warning"), ("error", "Error")],
        required=True,
        default="ok",
    )
    message = fields.Char()
    color = fields.Integer(compute="_compute_color")

    _sql_constraints = [
        (
            "connection_domain_unique",
            "unique(connection_id, domain)",
            "A connection has one synchronization status per domain.",
        )
    ]

    @api.depends("state")
    def _compute_color(self):
        for status in self:
            status.color = STATE_COLORS.get(status.state, 0)

    @api.depends("domain", "state")
    def _compute_display_name(self):
        labels = dict(self._fields["domain"].selection)
        states = dict(self._fields["state"].selection)
        for status in self:
            status.display_name = "{}: {}".format(
                labels.get(status.domain, status.domain or ""),
                states.get(status.state, status.state or ""),
            )
