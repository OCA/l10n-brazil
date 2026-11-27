# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Fiscal Document EDI: Purchase Requests",
    "summary": "Purchase request as a source of the origin of an imported fiscal "
    "document, and the order created from it",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "development_status": "Beta",
    "category": "Localisation",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "l10n_br_purchase_request",
        "l10n_br_purchase_edi",
    ],
    "data": [
        "security/security.xml",
        "views/document_view.xml",
        "views/document_match_view.xml",
        "views/purchase_request_view.xml",
    ],
    "demo": ["demo/purchase_request_edi_demo.xml"],
    "auto_install": True,
}
