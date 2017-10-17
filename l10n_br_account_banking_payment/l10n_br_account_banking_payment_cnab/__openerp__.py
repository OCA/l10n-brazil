# -*- coding: utf-8 -*-
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#    Copyright 2015 KMEE - www.kmee.com.br
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
    'name': 'Account Payment CNAB',
    'version': '0.1',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'external_dependencies': {
        'python': ['cnab240'],
    },
    'depends': [
        'l10n_br_account_payment_boleto',
        'l10n_br_account_payment_mode',
        'l10n_br_account_product',
        'account_banking_payment_export',
    ],
    'data': [
        'view/l10n_br_payment_cnab.xml',
        'view/payment_order.xml',
        'view/l10n_br_cnab_sequence.xml',
        'view/l10n_br_cobranca_cnab.xml',
        'view/l10n_br_cobranca_cnab_lines.xml',
        'view/account_move_line.xml',
        'view/res_partner_bank.xml',
        'view/payment_mode.xml',
        #'data/l10n_br_payment_export_type.xml',
        #'data/l10n_br_payment_mode.xml',
    ],
    'active': False,
    "installable": True,
    "auto_install": False,
}
