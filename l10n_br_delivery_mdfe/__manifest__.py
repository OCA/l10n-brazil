# Copyright (C) 2026 Madooit
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Delivery MDFe",
    "summary": "Integration between l10n_br_delivery and l10n_br_mdfe",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Madooit, Odoo Community Association (OCA)",
    "maintainers": ["rodmad85"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "depends": [
        "l10n_br_delivery",
        "l10n_br_mdfe",
    ],
    "data": [
        # Views
        "views/document.xml",
        "views/res_partner.xml",
    ],
    "installable": True,
    "auto_install": True,
}
