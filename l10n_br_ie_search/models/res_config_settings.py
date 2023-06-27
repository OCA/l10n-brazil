# Copyright 2023 KMEE - Breno Oliveira Dias
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ie_search = fields.Selection(
        [("sefaz", "SEFAZ"), ("sintegraws", "SINTEGRAWS")],
        string="Select IE search provider",
        config_parameter="l10n_br_ie_search.ie_search",
    )

    sintegra_token = fields.Char(
        string="SINTEGRA Token",
        config_parameter="l10n_br_ie_search.sintegra_token",
        default=False,
    )
