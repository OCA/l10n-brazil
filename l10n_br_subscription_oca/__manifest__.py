# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Subscription OCA",
    "summary": "Fiscal operation and taxes on OCA subscriptions and their invoices",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "depends": ["l10n_br_sale", "subscription_oca"],
    "data": [
        "views/sale_subscription_views.xml",
    ],
    "demo": [
        "demo/sale_subscription_demo.xml",
    ],
}
