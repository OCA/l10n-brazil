{
    "name": "Brazil Localization Setup & Test Integration",
    "summary": "Modules for Odoo's Brazil-focused usability with integration tests.",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Engenere, Odoo Community Association (OCA)",
    "maintainers": ["antoniospneto"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.1.0.3",
    "development_status": "Beta",
    "depends": [
        "account_reconcile_oca",
        "web_responsive",
        "web_theme_classic",
        "account_usability",
        # "mrp",
        #        "l10n_br_sale_stock",
        "base_technical_features",
        # Performance test framework moved here from l10n_br_account/l10n_br_sale
        # (needs AccountMoveBRCommon, the fiscal demo records and the fiscal
        # sale.order model).
        "l10n_br_account",
        "l10n_br_sale",
    ],
    "installable": True,
}
