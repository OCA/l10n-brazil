# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_br_sped_result_closing = fields.Boolean(
        string="Result Closing Entry",
        copy=False,
        help="Entry that brings the income and expense accounts to zero at the "
        "end of the assessment period, moving the result to the equity. The "
        "ECF reports the balance sheet after it and the result (K355, P150 and "
        "the revenue of the block P) before it.",
    )
