# Copyright 2020 KMEE
# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/lic enses/agpl).

{
    "name": "Base dos Planos de Contas",
    "summary": """
        Base do Planos de Contas brasileiros""",
    "version": "16.0.2.9.0",
    "license": "AGPL-3",
    "author": "Akretion, KMEE, Odoo Community Association (OCA)",
    "maintainers": ["renatonlima", "mileo"],
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["account"],
    "data": [
        # security
        "security/ir.model.access.csv",
        # Data
        # As etiquetas vêm ANTES do plano de propósito: ao carregar o
        # `account.chart.template`, o core cria a conta de transferência de
        # liquidez, e ela já nasce classificada (ver
        # `_prepare_transfer_account_template`). Na ordem inversa a etiqueta
        # ainda não existiria e a conta nasceria órfã.
        "data/account.account.tag.csv",
        "data/l10n_br_coa_template.xml",
        "data/account.tax.group.csv",
        "data/account.tax.template.csv",
        # Views
        "views/account_account.xml",
        "views/account_tax_template.xml",
        "views/account_tax.xml",
    ],
    "development_status": "Production/Stable",
    "installable": True,
}
