# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Creditability Test Suite",
    "summary": "Measures how recoverable taxes reach the stock cost, "
    "through the whole purchase cycle",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Localisation",
    "maintainers": ["DiegoParadeda"],
    "development_status": "Alpha",
    "depends": [
        "l10n_br_purchase_stock",
        "l10n_br_stock_account",
        "stock_picking_invoicing",
        # Conforto para inspecionar os ciclos de demonstracao na tela. Nenhum
        # teste depende deles, mas os dois vem de repositorios externos:
        # OCA/account-financial-tools e OCA/web.
        "account_usability",  # menus de lancamentos contabeis e o interruptor
        # de contabilidade anglo-saxonica, que o Odoo 16 nao expoe em tela
        "web_refresher",  # recarregar listas sem sair da tela
    ],
    "data": [],
    "demo": [
        "demo/creditability_case_1a.xml",
        "demo/creditability_case_1b.xml",
        "demo/creditability_case_2a.xml",
        "demo/creditability_case_2b.xml",
    ],
    "installable": True,
    "auto_install": False,
}
