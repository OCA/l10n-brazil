# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Módulo fiscal brasileiro",
    "summary": "Brazilian fiscal core module.",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Production/Stable",
    "version": "14.0.2.2.0",
    "depends": [
        "l10n_br_account",
    ],
    "data": [
        "views/document_view.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
