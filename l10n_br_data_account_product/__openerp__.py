# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

{
    'name': 'Brazilian Localisation Data Extension for Product',
    'description': 'Brazilian Localisation Data Extension for Product',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Brasil',
    'website': 'http://odoo-brasil.org',
    'version': '8.0',
    'depends': [
        'l10n_br_account_product',
        'l10n_br_data_account',
    ],
    'data': [
        'account.product.fiscal.classification.template.csv',
        'l10n_br_data_account_product_data.xml',
        #'account_fiscal_position_rule_data.xml',
    ],
    'demo': [
        'l10n_br_data_account_product_demo.xml',
    ],
    'category': 'Localisation',
    'installable': False,
    'auto_install': True,
}
