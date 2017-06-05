# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sped Vendas',
    'summary': """
        Vendas Brasileira""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'sped_imposto',
        'sale',
    ],
    'data': [
        # 'views/sale_order_line.xml',
        # 'security/sale_order.xml',
        'views/sale_order.xml',
    ],
    'demo': [
        'demo/sale_order.xml',
    ],
}
