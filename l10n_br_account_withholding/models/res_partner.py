# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # TODO: Add WH field for Country
    wh_cityhall = fields.Boolean(string="Is City Hall?", default=False)

    wh_state_treasury = fields.Boolean(
        string="Is State Treasury?",
        default=False,
        help="Partner that collects state taxes withheld in this state, "
        "such as ICMS. Used to fill the vendor of the withholding invoice "
        "when the fiscal tax group scope is 'State'.",
    )

    @api.constrains("state_id", "wh_state_treasury")
    def _check_unique_state_treasury(self):
        for record in self:
            if record.wh_state_treasury:
                existing_count = self.sudo().search_count(
                    [
                        ("state_id", "=", record.state_id.id),
                        ("wh_state_treasury", "=", True),
                        ("id", "!=", record.id),
                    ]
                )
                if existing_count > 0:
                    raise ValidationError(
                        _(
                            "Only one partner with the same State Treasury can "
                            "exist in the same state."
                        )
                    )

    @api.constrains("city_id", "wh_cityhall")
    def _check_unique_cityhall(self):
        for record in self:
            if record.wh_cityhall:
                existing_count = self.sudo().search_count(
                    [
                        ("city_id", "=", record.city_id.id),
                        ("wh_cityhall", "=", True),
                        ("id", "!=", record.id),
                    ]
                )
                if existing_count > 0:
                    raise ValidationError(
                        _(
                            "Only one partner with the same City Hall can "
                            "exist in the same city."
                        )
                    )
