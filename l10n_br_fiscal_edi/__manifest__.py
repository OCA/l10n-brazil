# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Common EDI fiscal features",
    "summary": "Common EDI fiscal features",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, KMEE, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima", "rvalyi", "mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "version": "16.0.1.8.0",
    "depends": [
        "l10n_br_fiscal",
    ],
    "data": [
        # security
        "security/ir.model.access.csv",
        # Views
        "views/document_view.xml",
        "views/invalidate_number_view.xml",
        "views/document_event_view.xml",
        "views/document_event_template.xml",
        # Reports
        "views/document_event_report.xml",
        # Wizards
        "wizards/document_cancel_wizard.xml",
        "wizards/document_correction_wizard.xml",
        "wizards/document_status_wizard.xml",
        "wizards/invalidate_number_wizard.xml",
        # Actions
        "views/l10n_br_fiscal_action.xml",
        # Menus
        "views/l10n_br_fiscal_menu.xml",
    ],
    "installable": True,
}
