# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Fiscal Document Notifications",
    "summary": "Define fiscal document notifications",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Production/Stable",
    "version": "16.0.1.1.0",
    "depends": [
        "l10n_br_fiscal",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/fiscal_security.xml",
        "data/l10n_br_fiscal_email_template.xml",
        "views/document_email_view.xml",
        "views/document_type_view.xml",
        "views/document_view.xml",
        "views/l10n_br_fiscal_action.xml",
        "views/l10n_br_fiscal_menu.xml",
    ],
    "demo": ["demo/l10n_br_fiscal_document_email.xml"],
    "installable": True,
}
