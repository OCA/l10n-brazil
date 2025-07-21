# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Product Contract",
    "summary": """
        Criação de contratos através dos Pedidos de Vendas""",
    "version": "16.0.1.1.2",
    "license": "AGPL-3",
    "author": "KMEE, Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "maintainers": ["mileo", "marcelsavegnago"],
    "depends": [
        "l10n_br_sale",
        "l10n_br_contract",
        "product_contract",
    ],
    "demo": [
        "demo/contract_template.xml",
        "demo/product.xml",
        "demo/sale_order.xml",
    ],
}
