# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Brazilian - Simple Accounting",
    "summary": "Brazilian Simple Chart of Account",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Akretion, " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "12.0.2.2.0",
    "depends": ["l10n_br_coa"],
    "data": [
        "data/l10n_br_coa_simple_template.xml",
        "data/account_group.xml",
        "data/account.account.template.csv",
        "data/account_tax_group.xml",
        "data/l10n_br_coa_simple_template_post.xml",
    ],
    "post_init_hook": "post_init_hook",
}
