# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Raphaël Valyi - Akretion                                #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

{
    'name': 'Brazilian Localization Sales and Warehouse',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, ,Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'sale_stock',
        'l10n_br_sale_product',
        'l10n_br_stock_account',
    ],
    'data': [
        'data/l10n_br_sale_stock_data.xml',
        'views/sale_stock_view.xml',
    ],
    'demo': [
        'l10n_br_sale_stock_demo.xml',
<<<<<<< HEAD
=======
        #'test/sale_order_demo.yml'
>>>>>>> comment data file
    ],
    'test': [
        'test/sale_order_demo.yml'
    ],
    'installable': True,
    'auto_install': True,
}
