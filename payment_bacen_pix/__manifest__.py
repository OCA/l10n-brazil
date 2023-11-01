# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Payment Bacen PIX",
    "summary": """
        Payment PIX with bacen""",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "account_payment",
    ],
    "data": [
        "views/payment_transfer_templates.xml",
        "data/payment_icon_data.xml",
        "data/payment_acquirer_data.xml",
        "views/payment_views.xml",
    ],
    "demo": [],
    "post_init_hook": "create_missing_journal_for_acquirers",
    "uninstall_hook": "uninstall_hook",
}
