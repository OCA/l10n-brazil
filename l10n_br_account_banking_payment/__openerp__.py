# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 - KMEE INFORMATICA LTDA (<http://kmee.com.br>).
#              Luis Felipe Miléo - mileo@kmee.com.br
#
#    All other contributions are (C) by their respective contributors
#
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Brazilian Account Banking - Debit and Payments Export Infrastructure',
    'version': '8.0.0.0.0',
    'license': 'AGPL-3',
    'author': "KMEE, "
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/odoo-brazil/odoo-brazil-banking',
    'category': 'Banking addons',
    'depends': [
        'l10n_br_account',
        'l10n_br_account',
        'account_banking_payment_export',
        ],
    'data': [
        'views/account_due_list.xml',
        'views/account_payment.xml',
        'views/payment_mode.xml',
        'views/payment_mode_type.xml',
        'wizard/payment_order_create_view.xml',
        'data/payment_mode_type.xml',
    ],
    'demo': [
        ],
    'installable': True,
}
