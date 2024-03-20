# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Brazilian Payment Order',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': "KMEE, "
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/l10n-brazil',
    'category': 'Banking addons',
    'depends': [
        'l10n_br_base',
        'account_payment_order',
        'account_due_list',
        'account_cancel',
    ],
    'data': [
        'views/account_due_list.xml',
        'views/account_payment_order.xml',
        'views/account_payment_order_menu_views.xml',
        'views/account_payment_line.xml',
        'views/account_payment_mode.xml',
    ],
    'demo': [
        'demo/account_payment_order_demo.xml',
        'demo/account_payment_mode_demo.xml'
    ],
    'installable': True,
}
