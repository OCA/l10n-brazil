# Copyright 2024 Marcel Savegnago - Escodoo (https://www.escodoo.com.br)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_account.models.account_move_line import (
    AccountMoveLine as AccountMoveLineBR,
)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    wh_move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="WH Account Move Line",
        ondelete="restrict",
    )

    def write(self, values):
        res = super(AccountMoveLineBR, self).write(values)
        for line in self:
            if line.wh_move_line_id and (
                "quantity" in values or "price_unit" in values
            ):
                raise UserError(
                    _("You cannot edit an invoice related to a withholding entry")
                )
        return res
