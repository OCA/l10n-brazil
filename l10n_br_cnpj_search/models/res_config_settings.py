# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cnpj_provider = fields.Selection(
        selection=[
            ("receitaws", "ReceitaWS"),
            ("serpro", "SERPRO"),
            ("cpfcnpj", "CPF.CNPJ"),
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

    cpfcnpj_token = fields.Char(
        string="CPF.CNPJ Token",
        config_parameter="l10n_br_cnpj_search.cpfcnpj_token",
    )

    cpfcnpj_package = fields.Selection(
        selection=[
            ("5", "5 - Cadastro e endereço"),
            ("6", "6 - Cadastro completo (Simples Nacional, porte e situação)"),
        ],
        string="CPF.CNPJ Package",
        default="6",
        config_parameter="l10n_br_cnpj_search.cpfcnpj_package",
    )

    cpfcnpj_skip_partners = fields.Boolean(
        string="CPF.CNPJ: do not import partners (QSA)",
        help="By default each partner from the QSA becomes a child contact. "
        "Enable this to skip that step.",
        config_parameter="l10n_br_cnpj_search.cpfcnpj_skip_partners",
    )

    cpfcnpj_skip_card = fields.Boolean(
        string="CPF.CNPJ: do not attach the CNPJ card PDF",
        help="By default the CNPJ card PDF returned by package 6 is attached "
        "to the partner. Enable this to skip that step.",
        config_parameter="l10n_br_cnpj_search.cpfcnpj_skip_card",
    )

    cpfcnpj_fetch_ie = fields.Boolean(
        string="CPF.CNPJ: fetch state registration (package 16)",
        default=False,
        config_parameter="l10n_br_cnpj_search.cpfcnpj_fetch_ie",
    )
