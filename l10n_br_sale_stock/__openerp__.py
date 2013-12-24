# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Raphaël Valyi - Akretion                                #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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
    'name': 'Brazilian Localization Sales and Warehouse',
    'description': 'Brazilian Localization for sale_stock_module',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERPBrasil.org',
    'website': 'http://openerpbrasil.org',
    'version': '7.0',
    'depends': [
        'sale_stock',
        'l10n_br_sale',
        'l10n_br_stock',
        'l10n_br_account_product',
    ],
    'data': [
        'l10n_br_sale_stock_data.xml',
        'sale_stock_view.xml',
    ],
    'demo': [
        'l10n_br_sale_stock_demo.xml',
        'test/sale_order_demo.yml' # put in demo rather than test for easier testing on Travis-CI
    ],
    'installable': True,
    'auto_install': True,
}
