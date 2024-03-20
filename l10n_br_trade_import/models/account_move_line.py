# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    import_addition_ids = fields.Many2many(
        comodel_name="l10n_br_trade_import.addition",
        relation="l10n_br_account_import_addition_move_line_rel",
        column1="move_line_id",
        column2="import_addition_id",
        string="Import Additions",
    )
