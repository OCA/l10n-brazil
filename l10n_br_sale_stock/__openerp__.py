# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Raphaël Valyi - Akretion                                #
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
    'name': 'l10n_br_sale_stock',
    'description': 'Brazilian Localization for sale_stock_module',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERPBrasil.org',
    'website': 'http://openerpbrasil.org',
    'version': '0.1',
    'depends': [
                'l10n_br_sale',
                'sale_stock',
               ],
    'init_xml': [],
    'update_xml': [
#                    'sale_stock_view.xml',
                    ],
    'demo_xml': [],
    'installable': True,
    'auto_install': True
}
