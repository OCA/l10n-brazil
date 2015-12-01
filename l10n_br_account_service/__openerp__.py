# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009-2013  Renato Lima - Akretion                             #
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
    'name': 'Brazilian Localization Account Service',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_br_account',
    ],
    'data': [
        'data/l10n_br_account_service_data.xml',
        'views/product_view.xml',
        'views/l10n_br_account_view.xml',
        'views/res_company_view.xml',
        'views/account_invoice_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/account_tax_demo.xml',
        'demo/product_demo.xml',
        'demo/l10n_br_account_service_demo.xml',
        'demo/account_fiscal_position_rule_demo.xml',
    ],
    'test': [
        'test/account_customer_invoice.yml',
        'test/account_supplier_invoice.yml',
        # 'test/account_invoice_refund.yml',
    ],
    'installable': True,
    'auto_install': False,
}
