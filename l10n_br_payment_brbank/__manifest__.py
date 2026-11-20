# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Payment Providers: brbank (boleto and Pix)",
    "summary": "Boletos and Pix charges in several Brazilian banks through brbank",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "depends": [
        "account",
        "payment",
        "l10n_br_payment",
        "l10n_br_bank_connection",
    ],
    # Module name only: a version specifier here breaks the import check.
    "external_dependencies": {"python": ["brbank"]},
    "data": [
        "security/ir.model.access.csv",
        "data/payment_provider_data.xml",
        "data/ir_cron.xml",
        "views/payment_provider_views.xml",
        "views/payment_transaction_views.xml",
        "views/boleto_instruction_views.xml",
        "views/brbank_event_views.xml",
        "views/account_payment_mode_views.xml",
        "views/account_move_views.xml",
        "views/portal_templates.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
