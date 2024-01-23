# © 2024 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PosConfig(models.Model):
    _name = "pos.cancel.reason"

    name = fields.Char(
        string="Cancel Reason",
        required=True,
        help="The reason will be shown in a POS Session.",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="If checked, it will allow you to show the reason in a POS Session.",
    )

    is_custom = fields.Boolean(
        string="Is Custom Reason",
        default=False,
        help="If checked, the reason will be a custom text field.",
    )
