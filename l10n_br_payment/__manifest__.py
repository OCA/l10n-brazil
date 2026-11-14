# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Payments: Boleto and Pix",
    "summary": "Base for boleto and Pix charges issued by payment providers",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "depends": [
        "payment",
        "account_payment",
        "account_payment_partner",
        "l10n_br_account_due_list",
        "l10n_br_base",
    ],
    "data": [
        "views/account_payment_mode.xml",
        "views/payment_transaction.xml",
        "views/report_invoice.xml",
        "views/portal_templates.xml",
    ],
    "demo": [],
}
