{
    "name": "Account NFe/NFC-e Integration",
    "summary": "Integration between account and NFe",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "12.0.0.0.0",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_nfe",
        "l10n_br_account",
        "account_payment_partner",
    ],
    "data": [
        "views/account_payment_mode.xml",
    ],
    "demo": [
        # Some demo data is being loaded via post_init_hook in hook file
    ],
}
