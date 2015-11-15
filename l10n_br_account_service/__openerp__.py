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
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '7.0',
    'depends': [
        'l10n_br_account',
    ],
    'data': [
        'data/l10n_br_account_service_data.xml',
        'product_view.xml',
        'l10n_br_account_view.xml',
        'res_company_view.xml',
        'account_invoice_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/account_tax_demo.xml',
        'demo/product_demo.xml',
    ],
    'test': [],
    'installable': False,
    'auto_install': False,
}
