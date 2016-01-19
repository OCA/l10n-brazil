# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo Brazil Account Payment Partner module for Odoo
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo <mileo@kmee.com.br>
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
    'name': 'Odoo Brazil Account Banking Payment Infrastructure',
    'version': '0.1',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'summary': '',
    'description': """ """,
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'depends': [
        'l10n_br_account',
        'l10n_br_data_base',
        'account_due_list_payment_mode',
        'account_banking_payment_export'
    ],
    'data': [
        'views/payment_mode_view.xml',
    ],
    'demo': [
        'demo/payment_demo.xml'
    ],
    'active': False,
}
