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
    'version': '8.0.1.0.0',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'http://www.kmee.com.br',
    'external_dependencies': {
        'python': ['cnab240',
                   'pyboleto'],
    },
    'depends': [
        'l10n_br_account_payment_boleto',
        'l10n_br_account_payment_mode',
        'l10n_br_account_product',
    ],
    'data': [
        'security/cnab_cobranca_security.xml',
        'view/l10n_br_payment_cnab.xml',
        'view/payment_order.xml',
        'view/l10n_br_cnab_sequence.xml',
        'view/l10n_br_cobranca_cnab.xml',
        'view/l10n_br_cobranca_cnab_lines.xml',
        'view/account_move_line.xml',
        'view/res_partner_bank.xml',
        'view/l10n_br_cnab_retorno_view.xml',
        'view/payment_mode.xml',
        'view/payment_line.xml',
        'view/bank_payment_line.xml',
        'data/l10n_br_payment_export_type.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        # 'demo/l10n_br_payment_mode.xml',
    ],
    'test': [
        'tests/invoice_create.yml'
    ],
    "installable": True,
    "auto_install": False,
}
