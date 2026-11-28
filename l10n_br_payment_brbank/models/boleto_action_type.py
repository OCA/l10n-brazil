# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BoletoActionType(models.Model):
    """What the Boleto actions assistant can do. A record, not a selection: the
    radio of the assistant filters it by a domain, per boleto, which a selection
    cannot do (the web client caches field descriptions per language)."""

    _name = "l10n_br.boleto.action.type"
    _description = "Boleto Action Type"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ("code_unique", "unique(code)", "The code of a boleto action must be unique.")
    ]
