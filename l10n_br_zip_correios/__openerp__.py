# -*- coding: utf-8 -*-
##############################################################################
#
#    Address from Brazilian Localization ZIP by Correios to Odoo
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Michell Stuttgart <michell.stuttgart@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Address from Brazilian Localization ZIP by Correios',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'version': '8.0.1.0.0',
    'website': 'http://odoo-brasil.org',
    'depends': [
        'l10n_br_zip',
    ],
    'test': [
        'test/company_zip.yml',
        'test/partner_zip.yml',
    ],
    'category': 'Localization',
    'installable': True,
    'external_dependencies': {
        'python': ['suds'],
    }
}
