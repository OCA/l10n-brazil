# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian Localization Account",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "http://github.com/OCA/l10n-brazil",
    "version": "12.0.1.0.1",
    "depends": [
	"account_cancel",
	"account_export_csv",
	"l10n_br_coa",
	"l10n_br_fiscal",
	],
    "data": [
        # security
        'security/ir.model.access.csv',
        'security/l10n_br_account_move_history.xml',
        'security/l10n_br_account_move_template.xml',

        # data
        "data/l10n_br_account_tax_data.xml",
        "data/l10n_br_account_tax_group_data.xml",

        "views/l10n_br_account_menu.xml",
        # Views
        "views/account_tax_view.xml",
        "views/account_tax_template_view.xml",
        "views/fiscal_tax_group_view.xml",
        "views/fiscal_operation_view.xml",
        'views/fiscal_operation_line_view.xml',
        'views/account_invoice_view.xml',
        'views/account_invoice_line_view.xml',
        'views/document_view.xml',
        'views/document_line_view.xml',
        'views/l10n_br_account_move_template_line.xml',
        'views/l10n_br_account_move_template.xml',
        'views/l10n_br_account_move_history.xml',

        # Wizards
        'wizards/account_invoice_refund_view.xml',
    ],
    "demo": [
        "demo/account_journal_demo.xml",
        "demo/fiscal_operation_demo.xml"
        'demo/l10n_br_account_move_history.xml',
        'demo/l10n_br_account_move_template_line.xml',
        'demo/l10n_br_account_move_template.xml',
    ],
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
}
