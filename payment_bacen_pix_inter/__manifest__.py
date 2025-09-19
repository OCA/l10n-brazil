# Copyright 2025 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Banco Inter PIX",
    "summary": "Integração PIX Banco Inter",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["payment_bacen_pix", "l10n_br_base"],
    "data": [
        "data/payment_provider.xml",
        "data/ir_cron.xml",
        "views/payment_provider_view_pix_inter.xml",
        "views/templates_pix_inter.xml",
    ],
    "installable": True,
    "application": False,
}
