# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cnpj_provider = fields.Selection(
        selection=[
            ("receitaws", "ReceitaWS"),
            ("serpro", "SERPRO"),
        ],
        string="CNPJ Search Provider",
        required=True,
        default="receitaws",
        config_parameter="l10n_br_cnpj_search.cnpj_provider",
    )

    serpro_token = fields.Char(
        string="SERPRO Token",
        config_parameter="l10n_br_cnpj_search.serpro_token",
    )

    serpro_trial = fields.Boolean(
        string="Use SERPRO Trial",
        config_parameter="l10n_br_cnpj_search.serpro_trial",
    )

    serpro_schema = fields.Selection(
        selection=[
            ("basica", "Básica"),
            ("qsa", "QSA"),
            ("empresa", "Empresa"),
        ],
        string="SERPRO Schema",
        config_parameter="l10n_br_cnpj_search.serpro_schema",
    )
