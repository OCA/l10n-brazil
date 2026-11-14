# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Payment Schedule",
    "summary": "Brazilian instruments in the payment schedule: boleto and guia "
    "with checked barcode, Pix with checked receiver, TED",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "category": "Localization",
    "depends": ["account_payment_schedule", "l10n_br_account_payment_order"],
    # Module name only: a version specifier here breaks the import check.
    "external_dependencies": {"python": ["brbank"]},
    "data": [
        "security/ir.model.access.csv",
        "wizards/payment_instrument_reader_views.xml",
        "views/account_move_line_views.xml",
    ],
    "pre_init_hook": "pre_init_hook",
}
