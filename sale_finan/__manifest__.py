# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

{
    'name': 'Finan Vendas',
    'summary': 'Finan Vendas',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': u'Odoo Community Association (OCA), Ari Caldeira',
    'depends': [
        'sped_sale',
        'finan',
    ],
    'data': [
        'views/inherited_account_payment_term_view.xml',
        'views/inherited_sale_order_orcamento_view.xml',
    ],
    'installable': True,
    'auto_install': True,
}
