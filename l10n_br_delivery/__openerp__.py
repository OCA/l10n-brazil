# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2010  Renato Lima - Akretion                                  #
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
    'name': 'Delivery for Brazilian Localization',
    'description': 'Extend delivery module for Brazilian Localization',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '0.6',
    'depends': [
        'l10n_br_stock',
        'l10n_br_sale',
        'delivery',
    ],
    'init_xml': [],
    'update_xml': [
        'account_invoice_view.xml',
        'delivery_view.xml',
        'sale_view.xml',
        'stock_view.xml',
        'l10n_br_delivery_view.xml',
        'security/ir.model.access.csv',
    ],
    'category': 'Localisation',
    'active': False,
    'installable': True
}
