# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Fiscal Document EDI: Purchases",
    "summary": "Where an imported fiscal document came from: purchase order, "
    "quotation or none",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "development_status": "Beta",
    "category": "Localisation",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_purchase", "l10n_br_account_edi"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/document_match_view.xml",
        "views/document_view.xml",
        "views/purchase_order_view.xml",
    ],
    "demo": ["demo/purchase_edi_demo.xml"],
    "auto_install": True,
}
