# -*- coding: utf-8 -*-
##############################################################################
#
#    Módulo Odoo para Terminal de Pagamento do POS
#    © 2018 KMEE INFORMATICA LTDA <https://kmee.com.br>
#
##############################################################################


{
    'name': 'l10n_br_tef',
    'version': '8.0.0.1.0',
    'category': 'Point Of Sale',
    'summary': 'Manage Payment Terminal device from POS front end',
    'author': "KMEE Informatica LTDA",
    'license': 'AGPL-3',
    'depends': ['point_of_sale'],
    'data': [
        'l10n_br_tef.xml',
        'l10n_br_tef_view.xml',
        ],
    'demo': ['l10n_br_tef_demo.xml'],
    'qweb': ['static/src/xml/l10n_br_tef.xml'],
}
