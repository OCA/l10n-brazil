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
    'name': 'Brazilian Localization Purchase',
    'description': 'Brazilian Localization for Purchase',
    'license': 'AGPL-3',
    'category': 'Localisation',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '0.6',
    'depends': [
        'l10n_br_account',
        'account_fiscal_position_rule_purchase',
    ],
    'data': [
        'l10n_br_purchase_data.xml',
        'purchase_view.xml',
        'res_company_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_purchase_security.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': True
}
