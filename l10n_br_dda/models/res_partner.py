# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    dda_assignee_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="l10n_br_dda_partner_assignee_rel",
        column1="partner_id",
        column2="assignee_id",
        string="DDA assignees",
        help="Partners (factoring, securitization, collection platforms) that "
        "may issue boletos in the name of this vendor. A boleto of an assignee "
        "is suggested for this vendor as an assignment, never linked by itself.",
    )
