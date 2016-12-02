# -*- coding: utf-8 -*-
# @ 2016 Kmee - www.kmee.com.br - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization WMS Accounting Report',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_br_stock_account',
        'report_xls',
    ],
    'data': [
        'wizard/stock_valuation_history_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': False,
    'auto_install': True,
}
