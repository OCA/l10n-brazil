# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cnpj_update_days = fields.Integer(
        config_parameter="l10n_br_cnpj.cnpj_update_days",
        default=365,
        string="Days to Update CNPJ",
    )

    cnpj_provider = fields.Selection(
        selection=[
            ("receitaws", "ReceitaWS"),
            ("serpro", "SERPRO"),
        ],
        string="CNPJ Search Provider",
        required=True,
        default="receitaws",
        config_parameter="l10n_br_cnpj.cnpj_provider",
    )
