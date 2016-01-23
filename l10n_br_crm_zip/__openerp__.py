# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2011  Fabio Negrini                                           #
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
    'name': 'Brazilian Localization CRM Zip',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'Fabio Negrini, Odoo Community Association (OCA)',
    'website': 'http://odoobrasil.org',
    'version': '8.0.1.0.1',
    'depends': [
        'l10n_br_zip',
        'l10n_br_crm',
    ],
    'data': [
        'views/crm_lead_view.xml',
        'views/crm_opportunity_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
