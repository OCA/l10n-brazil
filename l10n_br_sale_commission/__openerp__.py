# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'L10n BR Sale Commission',
    'version': '8.0.0.0.0',
    'category': 'Sale',
    'license': 'AGPL-3',
    'summary': 'Sale commissions computed without tax',
    'author': "KMEE,"
              "Odoo Community Association (OCA)",
    'website': 'http://www.kmee.com.br',
    'depends': [
        'l10n_br_sale_product',
        'sale_commission'
               ],
    'data': [
        'view/account_invoice_view.xml'
    ],
    'demo': [
        'demo/commission_demo.xml'
    ],
    'installable': True,
    'active': False,
}
