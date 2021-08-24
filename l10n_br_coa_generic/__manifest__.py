# Copyright (C) 2020 Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Plano de Contas para empresas do Regime normal",
    "summary": """Plano de Contas para empresas do Regime normal
        (Micro e pequenas empresas)""",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "KMEE, " "Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "development_status": "Production/Stable",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "13.0.1.0.0",
    "depends": ["l10n_br_coa"],
    "data": [
        "data/l10n_br_coa_generic_template.xml",
        "data/account_group.xml",
        "data/account.account.template.csv",
        "data/account_tax_group.xml",
        "data/account_fiscal_position_template.xml",
        "data/l10n_br_coa_generic_template_post.xml",
    ],
    "post_init_hook": "post_init_hook",
}
