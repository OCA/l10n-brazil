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
    'name' : 'Brazilian Localization Base',
    'description' : 'Brazilian Localization Base',
    'category' : 'Localisation',
    'license': 'AGPL-3',
    'author' : 'Akretion, OpenERP Brasil',
    'website' : 'http://openerpbrasil.org',
    'version' : '0.6',
    'depends' : ['base'],
    'init_xml': [
                'res.country.state.csv',
                'l10n_br_base.city.csv',
                ],
    'update_xml' : [
                    'l10n_br_base_data.xml',
                    'l10n_br_base_view.xml',
                    'res_country_view.xml',
                    'wizard/l10n_br_base_zip_search_view.xml',
                    'partner_view.xml',
                    'security/ir.model.access.csv',
                    'security/l10n_br_base_security.xml',
                    ],
    'test': [
            'test/base_inscr_est_valid.yml',
            'test/base_inscr_est_invalid.yml',
            ],
    'demo_xml': ['l10n_br_base_demo.xml'],
    'installable': True
}
