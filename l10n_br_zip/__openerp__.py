# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2009  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

{
    'name': 'Brazilian Localisation ZIP Codes',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'version': '8.0.1.0.1',
    'depends': [
        'l10n_br_base',
    ],
    'data': [
        'views/l10n_br_zip_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'wizard/l10n_br_zip_search_view.xml',
        'security/ir.model.access.csv',
    ],
    'test': ['test/zip_demo.yml'],
    'category': 'Localization',
    'installable': True,
}
