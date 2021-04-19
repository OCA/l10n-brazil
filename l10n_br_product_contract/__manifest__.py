# Copyright 2021 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Product Contract',
    'summary': """
        Criação de contratos através dos Pedidos de Vendas""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/l10n-brazil.git',
    'development_status': 'Beta',
    'maintainers': ['mileo'],
    'depends': [
        'l10n_br_contract',
        'product_contract',
    ],
    'data': [
    ],
    'demo': [
        'demo/sale_order.xml',
    ],
}
