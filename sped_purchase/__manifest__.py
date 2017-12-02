# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sped Compras',
    'summary': """
        Compras Brasileira""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'sped_imposto',
        'sped',
        'purchase',
        'sped_stock',
    ],
    'data': [
        # 'security/purchase_order_line.xml',
        # 'security/purchase_order.xml',
        'views/purchase_order_line.xml',
        'views/purchase_order.xml',
        'views/sped_documento_emissao_nfe_view.xml',
        'views/sped_documento_item.xml',
        'views/stock_picking.xml',
        'wizard/sped_consulta_status_documento.xml',
    ],
    'demo': [
        # 'demo/purchase_order_line.xml',
        # 'demo/purchase_order.xml',
    ],
    'installable': True,
}
