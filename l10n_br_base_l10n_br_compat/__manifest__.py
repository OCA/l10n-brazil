# Copyright (C) 2025 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "l10n_br Compatibility",
    "summary": "Compatibility with the l10n_br module",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["rvalyi"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_base", "l10n_br"],
    "version": "18.0.2.0.0",
    "data": [
        "views/res_partner_views.xml",
        "views/res_company_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
}
