# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Account Payment Order Brbank",
    "summary": "Send Brazilian payment orders (boleto, guia, Pix, TED) through the "
    "bank API with the brbank library",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "category": "Localization",
    "depends": [
        "account_payment_order_api",
        "l10n_br_account_payment_order",
        "l10n_br_bank_connection",
        "l10n_br_payment_schedule",
    ],
    # Module name only: a version specifier here breaks the import check.
    "external_dependencies": {"python": ["brbank"]},
    "data": [
        "views/account_payment_mode_views.xml",
        "views/account_payment_order_views.xml",
        "views/bank_connection_views.xml",
    ],
}
