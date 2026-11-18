# Copyright (C) 2019  Renato Lima (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cep_update_days = fields.Integer(
        config_parameter="l10n_br_zip.cep_update_days",
        default=365,
        string="Days to Update CEP",
    )

    cep_ws_provider = fields.Selection(
        selection=[
            ("apicep", "API CEP"),
            ("viacep", "VIA CEP"),
        ],
        string="ZIP Search Provider",
        required=True,
        default="viacep",
        config_parameter="l10n_zip.cep_ws_provider",
    )
