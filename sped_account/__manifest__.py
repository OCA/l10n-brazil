# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

{
    'name': u'SPED - Account',
    'version': '10.0.1.0.0',
    'author': u'"Odoo Community Association (OCA), Ari Caldeira',
    'category': u'Base',
    'depends': [
        'sped',
        'account',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'data': [
        # 'data/inherited_product_uom_category_data.xml',
        # 'data/inherited_product_uom_data.xml',
        # 'data/inherited_sped_unidade_data.xml',

        'views/inherited_account_invoice_view.xml',
    ]
}
