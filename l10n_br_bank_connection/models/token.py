# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankConnectionToken(models.Model):
    """Access token of a connection, shared between the workers."""

    _name = "l10n_br_bank_connection.token"
    _description = "Bank Connection Access Token"

    connection_id = fields.Many2one(
        comodel_name="l10n_br_bank_connection.connection",
        required=True,
        ondelete="cascade",
        index=True,
    )
    key = fields.Char(required=True, help="Account and scope of the token.")
    value = fields.Char(required=True)
    expires_at = fields.Float(
        required=True, digits=(16, 3), help="Expiry as epoch seconds."
    )

    _sql_constraints = [
        (
            "connection_key_unique",
            "unique(connection_id, key)",
            "A connection has one token per key.",
        )
    ]
