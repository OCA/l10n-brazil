# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "NF-e",
    "summary": "Brazilian Eletronic Invoice NF-e .",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, " "Odoo Community Association (OCA)",
    "website": "http://github.com/OCA/l10n-brazil",
    "version": "12.0.1.0.0",
    "depends": [
        "l10n_br_fiscal",
        "l10n_br_nfe_spec",
        ],
    "data": [
        'l10n_br_fiscal',
        'l10n_br_nfe_spec',
        # Security
        "security/nfe_security.xml",
#        'security/ir.model.access.csv',
        # Views
        "views/res_company_view.xml",
        "views/nfe_document_view.xml",
        "views/nfe_document_line_view.xml",
        "views/res_config_settings_view.xml",
        # Action
        "views/nfe_action.xml",
        # Menu
        # "views/nfe_menu.xml",
    ],
    'post_init_hook': 'post_init_hook',
    "installable": True,
    "auto_install": False,
}
