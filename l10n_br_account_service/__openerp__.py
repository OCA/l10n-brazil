# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009-2013  Renato Lima - Akretion                             #
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
    'name': 'Brazilian Localization Account Service',
    'description': 'Brazilian Localization Account Service',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Brasil',
    'website': 'http://odoo-brasil.org',
    'version': '8.0',
    'depends': [
        'l10n_br_account',
    ],
    'data': [
        'data/l10n_br_account_service_data.xml',
        'views/product_view.xml',
        'views/l10n_br_account_view.xml',
        'views/res_company_view.xml',
        'views/account_invoice_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/account_tax_demo.xml',
        'demo/product_demo.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
