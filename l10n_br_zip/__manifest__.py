# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localisation ZIP Codes",
    "summary": "Brazilian Localisation ZIP Codes",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, " "Odoo Community Association (OCA)",
    "maintainers": ["renatonlima"],
    "website": "http://odoo-brasil.org",
    "version": "12.0.3.0.1",
    "depends": ["l10n_br_base"],
    "data": [
        "views/l10n_br_zip_view.xml",
        "views/res_partner_address_view.xml",
        "views/res_config_settings_view.xml",
        "wizard/l10n_br_zip_search_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "development_status": "Mature",
    "external_dependencies": {"python": ["pycep_correios"]},
}
