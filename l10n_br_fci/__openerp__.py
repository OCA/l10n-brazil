# -*- encoding: utf-8 -*-
##############################################################################
#
#    Brazillian 5 acts module for OpenERP
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Bianca Tella <bianca.tella@kmee.com.br>
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
    'name': 'FCI',
    'version': '8.0.1.0.0',
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'category': 'Localization',
    'sequence': 64,
    'depends': [
        'l10n_br_account_product',
        'mrp',
    ],
    'data': [
        'wizard/products_from_product_template_view.xml',
        'views/l10n_br_fci.xml',
        'workflow/fci_workflow.xml',
        'views/product.xml',
        'data/product_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,

}
