# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Plano de Contas para Pequena Empresa (ITG 1000)",
    "summary": "Plano de Contas ITG 1000 para Microempresas e Empresa de Pequeno Porte",
    "category": "Accounting/Localizations/Account Charts",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima"],
    "development_status": "Production/Stable",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "19.0.1.0.0",
    "depends": ["l10n_br_coa"],
    "data": [],
    "post_init_hook": "post_init_hook",
    "oca_data_manual": [
        "demo/account_journal.xml",
    ],
}
