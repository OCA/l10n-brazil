# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sped Estoque',
    'summary': """
        Estoque Brasileira""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'sped_imposto',
        'stock',
    ],
    'data': [

        # 'security/sale_order.xml',

        'views/stock_picking_view.xml',
        'views/stock_move_view.xml',
        'views/sped_operacao_view.xml',
    ],
    'demo': [
        # 'demo/sale_order.xml',
    ],
    'installable': True,
}
