# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Payment Partner module for OpenERP
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
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
    'name': 'Account Payment Boleto on Move Line',
    'version': '0.1',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'summary': 'Adds payment mode boleto on move lines',
    'description': """ """,
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'depends': ['account_payment_move_line'],
    'data': [
        'view/payment_mode.xml',
        'view/account_move_line.xml',
        'report_print_button_view.xml',
    ],
    'demo': [
    ],
    'active': False,
}
