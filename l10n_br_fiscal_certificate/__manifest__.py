# Copyright (C) 2023  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "A1 fiscal certificate management for Brazil",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Production/Stable",
    "version": "16.0.1.1.0",
    "depends": [
        "l10n_br_fiscal",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/certificate_view.xml",
        "views/res_company_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
    "external_dependencies": {
        "python": [
            "erpbrasil.assinatura>=1.7.0",
        ]
    },
}
