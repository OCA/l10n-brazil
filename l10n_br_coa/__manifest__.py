# Copyright 2020 KMEE
# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/lic enses/agpl).

{
    "name": "Base dos Planos de Contas",
    "summary": """
        Base do Planos de Contas brasileiros""",
    "version": "18.0.3.3.1",
    "license": "AGPL-3",
    "author": "Akretion, KMEE, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima", "mileo"],
    "category": "Accounting/Localizations/Account Charts",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["account"],
    "data": [
        # security
        # Data
        # "data/l10n_br_coa_template.xml",
        # As etiquetas vêm ANTES do plano de propósito: ao carregar o
        # `account.chart.template`, o core cria a conta de transferência de
        # liquidez, e ela já nasce classificada (ver
        # `_get_accounts_data_values`). Na ordem inversa a etiqueta
        # ainda não existiria e a conta nasceria órfã.
        "data/account.account.tag.csv",
        # "data/template/account.tax.group.csv",
        # "data/template/account.tax.csv",
        #        "data/account.tax.template.csv",
        # Views
        "views/account_account.xml",
        "views/account_tax.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_br_coa/static/src/js/account_tax_withholding.esm.js",
        ],
    },
    "development_status": "Production/Stable",
    "installable": True,
}
