# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Documentos fiscais Subsequentes",
    "summary": "Documentos Fiscais Subsequentes",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "version": "16.0.1.2.0",
    "depends": [
        "l10n_br_fiscal",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/subsequent_operation_view.xml",
        "views/subsequent_document_view.xml",
        "views/l10n_br_fiscal_action.xml",
        "views/l10n_br_fiscal_menu.xml",
    ],
    "demo": [
        "demo/subsequent_operation_demo.xml",
    ],
}
