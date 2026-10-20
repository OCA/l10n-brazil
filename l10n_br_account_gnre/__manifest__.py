# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "GNRE Accounting Integration",
    "summary": """Integration between l10n_br_account and l10n_br_gnre""",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_gnre",
        "l10n_br_account",
        "l10n_br_account_withholding",
    ],
    "data": [
        "views/gnre_state_config.xml",
        "views/account_move.xml",
    ],
    "installable": True,
    "auto_install": True,
}
