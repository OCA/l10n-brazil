# Copyright 2023 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization IE Search",
    "summary": """
        Integração com a API SintegraWS e SEFAZ""",
    "version": "15.0.1.2.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_cnpj_search", "l10n_br_nfe"],
    "data": ["views/res_config_settings_view.xml"],
    "external_dependencies": {
        "python": [
            "erpbrasil.base",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.assinatura",
            "erpbrasil.edoc>=2.5.2",
        ]
    },
}
