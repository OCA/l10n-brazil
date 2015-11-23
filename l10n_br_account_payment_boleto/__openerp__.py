# -*- coding: utf-8 -*-
##############################################################################
#
#    Account Payment Boleto module for Odoo
#    Copyright (C) 2012-2015 KMEE (http://www.kmee.com.br)
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
    'name': 'Odoo Brasil Account Payment Boleto',
    'version': '0.1',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'summary': 'Adds payment mode boleto on move lines',
    'description': """ """,
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'depends': [
        'l10n_br_account_payment_mode',
        'base_transaction_id',
    ],
    'data': [
        'data/boleto_data.xml',
        'views/res_company.xml',
        'views/payment_mode.xml',
        'views/account_move_line.xml',
        'reports/report_print_button_view.xml',
    ],
    'demo': [
        'demo/payment_demo.xml',
    ],
    'active': False,
}
