# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Invoicing and accounting entries for Brazil",
    "summary": "Invoicing and accounting entries for Brazil",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.7.2.0",
    "development_status": "Beta",
    "maintainers": ["renatonlima", "rvalyi"],
    "depends": [
        "l10n_br_coa",
        "l10n_br_fiscal",
        "l10n_br_account_due_list",
    ],
    "data": [
        # security
        "security/ir.model.access.csv",
        "security/l10n_br_account_security.xml",
        # data
        "data/account_tax_group.xml",
        "data/account_tax_template.xml",
        # Views
        "views/account_tax_view.xml",
        "views/account_tax_template_view.xml",
        "views/fiscal_operation_view.xml",
        "views/fiscal_operation_line_view.xml",
        "views/account_move_view.xml",
        "views/document_line_view.xml",
        "views/document_view.xml",
        "views/fiscal_invoice_view.xml",
        "views/fiscal_invoice_line_view.xml",
        # Wizards
        "wizards/account_move_reversal_view.xml",
        "wizards/wizard_document_status.xml",
        "wizards/document_import_wizard_mixin.xml",
        # Actions
        "views/l10n_br_account_action.xml",
        # Menus
        "views/l10n_br_account_menu.xml",
        # Report
        #        "report/account_invoice_report_view.xml",
        "views/res_partner_view.xml",
    ],
    "demo": [
        "demo/res_users_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
}
