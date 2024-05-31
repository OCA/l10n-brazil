# Copyright 2023 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization CNPJ Search",
    "summary": """
        Integração com os Webservices da ReceitaWS e SerPro""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "l10n_br_zip",
        "l10n_br_fiscal",
        "contacts",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
        "views/res_company_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "demo": [],
}
