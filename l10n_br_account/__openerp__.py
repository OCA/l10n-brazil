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
    'name': 'Brazilian Localization Account',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoobrasil.org',
    'version': '8.0.1.1.0',
    'depends': [
        'l10n_br',
        'l10n_br_base',
        'account_cancel',
        'account_fiscal_position_rule',
        'web_context_tunnel',
    ],
    'data': [
        'l10n_br_account_workflow.xml',
        'account_fiscal_position_workflow.xml',
        'data/l10n_br_account.fiscal.document.csv',
        'data/l10n_br_account_data.xml',
        'views/account_view.xml',
        'views/account_fiscal_position_rule_view.xml',
        'views/account_invoice_view.xml',
        'views/l10n_br_account_view.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml',
        'views/res_company_view.xml',
        'views/res_config_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_account_security.xml',
        'report/account_invoice_report_view.xml',
    ],
    'demo': [
        'demo/account.account.csv',
        'demo/account_tax_code.xml',
        'demo/account_financial_demo.xml',
        'demo/account_fiscal_demo.xml',
        'demo/base_demo.xml',
    ],
    'test': [
        'test/account_customer_invoice.yml',
        'test/account_supplier_invoice.yml',
        'test/generate_fiscal_rules.yml',
    ],
    'installable': True,
    'auto_install': False,
}
