# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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
    'name': 'Brazilian Localization Account Product',
    'description': """Brazilian Localization Account Product""",
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '7.0',
    'depends': [
        'l10n_br_account',
        'account_product_fiscal_classification',
    ],
    'data': [
        'l10n_br_account_product_view.xml',
        'l10n_br_account_product_sequence.xml',
        'data/l10n_br_account_product.cfop.csv',
        'data/l10n_br_account.fiscal.document.csv',
        'data/l10n_br_account_product_data.xml',
        'l10n_br_account_view.xml',
        'l10n_br_account_product_view.xml',
        'account_view.xml',
        'account_invoice_view.xml',
        'account_invoice_workflow.xml',
        'res_partner_view.xml',
        'res_company_view.xml',
        'account_product_fiscal_classification_view.xml',
        'product_view.xml',
        'wizard/l10n_br_account_nfe_export_invoice_view.xml',
        'wizard/l10n_br_account_nfe_export_view.xml',
        'wizard/l10n_br_account_nfe_status_sefaz_view.xml',
        'security/l10n_br_account_product_security.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/account_tax_code_demo.xml',
        'demo/account_tax_demo.xml',
        'demo/l10n_br_account_product_demo.xml',
        'demo/l10n_br_data_account_product_demo.xml',
        'demo/product_demo.xml',
        'demo/product_taxes.yml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
