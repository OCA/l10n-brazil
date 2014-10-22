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
    'name': 'Brazilian Localization Base',
    'description': 'Brazilian Localization Base',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '7.0',
    'depends': [
        'base',
    ],
    'data': [
        'res.country.state.csv',
        'l10n_br_base.city.csv',
        'l10n_br_base_data.xml',
        'l10n_br_base_view.xml',
        'res_country_view.xml',
        'res_partner_view.xml',
        'res_company_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_base_security.xml',
    ],
    'demo': [
        'l10n_br_base_demo.xml',
    ],
    'test': [
        'test/base_inscr_est_valid.yml',
        'test/base_inscr_est_invalid.yml',
    ],
    'installable': True,
    'auto_install': False,
}
