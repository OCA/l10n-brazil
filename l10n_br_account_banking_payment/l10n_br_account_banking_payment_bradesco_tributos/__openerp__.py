# -*- coding: utf-8 -*-
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#    Author: Luiz Felipe do Divino
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
    'name': 'Account Payment Tributos Bradesco',
    'version': '0.1',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'external_dependencies': {
        'python': ['fixedwidth'],
    },
    'depends': [
        'l10n_br_account_payment_mode',
        'l10n_br_account_banking_payment',
    ],
    'data': [
        'view/l10n_br_payment_tax.xml',
        'view/l10n_br_cobranca_tax.xml',
        'view/payment_mode.xml',
        'view/guia_recolhimento.xml',
    ],
    "installable": True,
    "auto_install": False,
}
