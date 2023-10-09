# Copyright (C) 2019  Renan Hiroki Bastos - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


{
    "name": "NF-e Stock Integration",
    "summary": "Brazilian Eletronic Invoice NF-e",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE," "Odoo Community Association (OCA)",
    "maintainers": [],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "version": "14.0.13.0.0",
    "depends": [
        "l10n_br_nfe",
        "l10n_br_purchase_stock",
    ],
    "data": [
        # Views
        "views/document_view.xml",
        "views/picking_view.xml",
        "views/purchase_view.xml",
        # Wizards
        "wizards/import_document.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
