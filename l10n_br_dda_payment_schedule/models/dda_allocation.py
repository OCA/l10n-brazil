# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DdaAllocation(models.Model):
    _inherit = "l10n_br_dda.allocation"

    payment_schedule_state = fields.Selection(
        related="move_line_id.payment_schedule_state"
    )
