# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br DDA",
    "summary": "DDA inbox: boletos registered against your CNPJ, matched to vendor "
    "bills and sent to payment",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "category": "Accounting/Localizations",
    "depends": [
        "l10n_br_account_payment_order",
        "l10n_br_cnab_structure",
        "mail",
    ],
    "data": [
        "security/dda_security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/dda_debit_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "views/cnab_structure_views.xml",
        "wizards/dda_match_wizard_views.xml",
        "wizards/dda_ignore_wizard_views.xml",
        "wizards/dda_import_wizard_views.xml",
        "views/dda_menus.xml",
    ],
    "demo": [
        "demo/dda_cnab_structure_demo.xml",
        "demo/dda_demo.xml",
    ],
    "assets": {
        "web.assets_backend": ["l10n_br_dda/static/src/**/*"],
        "web.assets_tests": ["l10n_br_dda/static/tests/tours/**/*"],
        "web.assets_unit_tests": ["l10n_br_dda/static/tests/**/*.test.js"],
    },
}
