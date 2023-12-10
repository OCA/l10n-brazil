# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009-2013  Renato Lima - Akretion                             #
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
    'name': 'Brazilian Localization Account',
    'description': 'Brazilian Localization Account',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '0.6',
    'depends': [
        'l10n_br',
        'l10n_br_base',
        'l10n_br_product',
        'account_fiscal_position_rule',
        'account_product_fiscal_classification',
    ],
    'data': [
        'data/l10n_br_account.fiscal.document.csv',
        'data/l10n_br_account.cfop.csv',
        'data/l10n_br_account_data.xml',
        'account_view.xml',
        'l10n_br_account_sequence.xml',
        'account_fiscal_position_rule_view.xml',
        'account_invoice_view.xml',
        'account_invoice_workflow.xml',
        'l10n_br_account_view.xml',
        'res_partner_view.xml',
        'product_view.xml',
        'res_company_view.xml',
        'account_product_fiscal_classification_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_account_security.xml',
        'wizard/l10n_br_account_nfe_export_invoice_view.xml',
        'wizard/l10n_br_account_nfe_export_view.xml',
    ],
    'demo': [
        'demo/account.account.csv',
        'demo/account_tax_code.xml',
        'demo/account_tax.xml',
        'demo/account_financial_demo.xml',
        'demo/account_fiscal_demo.xml',
        'demo/base_demo.xml',
        #'demo/product_demo.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': True,
}
