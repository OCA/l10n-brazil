# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants import DEBIT_MODEL, SOURCE_TYPES


class DdaDebitSource(models.Model):
    _name = "l10n_br_dda.debit.source"
    _description = "DDA boleto source"
    _order = "last_seen desc, id desc"

    debit_id = fields.Many2one(
        comodel_name=DEBIT_MODEL, required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="debit_id.company_id", store=True)
    source_type = fields.Selection(selection=SOURCE_TYPES, required=True)
    source_key = fields.Char(
        required=True,
        help="Where the boleto came from, for instance connection:5 or cnab:<hash>.",
    )
    external_id = fields.Char(help="Identifier of the boleto at the source.")
    last_seen = fields.Datetime(default=fields.Datetime.now)

    _sql_constraints = [
        (
            "unique_source",
            "unique(debit_id, source_type, source_key)",
            "The boleto already has this source.",
        )
    ]
