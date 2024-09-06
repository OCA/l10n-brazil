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
    "version": "14.0.1.0.0",
    "depends": [
        "l10n_br_fiscal",
    ],
    "data": [
        # Data
        "data/l10n_br_fiscal_email_template.xml",
        # Views
        "views/document_email_view.xml",
        # Actions
        "views/l10n_br_fiscal_action.xml",
        # Menus
        "views/l10n_br_fiscal_menu.xml",
    ],
    "demo": ["demo/l10n_br_fiscal_document_email.xml"],
    "installable": True,
}
