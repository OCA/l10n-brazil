# Copyright 2024 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class SpecMixinFAKE(models.AbstractModel):
    _name = "l10n_br_sped.mixin.fake"
    _description = "l10n_br_sped.mixin.fake"
    _inherit = "l10n_br_sped.mixin"

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_sped.fake.0000",
        required=True,
    )

    state = fields.Selection(related="declaration_id.state")
