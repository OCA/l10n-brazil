# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
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
    'name': 'Brazilian Localization Account withholdings',
    'description': """
    Brazilian Localization Account withholdings""",
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'version': '7.0',
    'depends': [
        'l10n_br_account_product',
    ],
    'data': [
        'account_invoice_view.xml',
        'l10n_br_account_view.xml',
        'res_company_view.xml',
    ],
    'installable': True
}
