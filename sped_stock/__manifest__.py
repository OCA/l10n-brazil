# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sped Estoque',
    'summary': """
        Estoque Brasileiro""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'sped_imposto',
        'sped',
        'sped_nfe',
        'stock',
    ],
    'data': [
        'views/stock_move_entrada_saida_view.xml',

        'views/inherited_sped_produto_produto_view.xml',
        'views/inherited_sped_operacao_base_view.xml',
        'views/inherited_sped_documento_base_view.xml',

        'views/inherited_stock_picking_type_view.xml',
        'views/inherited_stock_picking_view.xml',
        'views/inherited_stock_move_view.xml',

        #
        # Permissões e grupos
        #
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': True,
}
