# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009 - TODAY Renato Lima - Akretion                           #
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
    'name': 'Brazilian Localization Base',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.1',
    'depends': [
        'base',
    ],
    'data': [
        'data/res.country.state.csv',
        'data/l10n_br_base.city.csv',
        'data/l10n_br_base_data.xml',
        'views/l10n_br_base_view.xml',
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/base_demo.xml',
        'demo/l10n_br_base_demo.xml',
        'demo/res_partner_demo.xml',
    ],
    'test': [
        'test/base_inscr_est_valid.yml',
        'test/base_inscr_est_invalid.yml',
        'test/res_partner_test.yml',
        'test/res_company_test.yml',
    ],
    'installable': True,
    'auto_install': False,
}
