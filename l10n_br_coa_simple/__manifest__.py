# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Plano de Contas do Simples ITG 1000",
    "summary": "Plano de Contas ITG 1000 para Microempresas e Empresa de Pequeno Porte",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Akretion, " "Odoo Community Association (OCA)",
    "maintainers": ["renatonlima"],
    "development_status": "Production/Stable",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "13.0.1.0.0",
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
