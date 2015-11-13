# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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
    'name': 'Brazilian Localization Account Product',
    'summary': "Brazilian Localization Account Product",
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.2.0.0',
    'depends': [
        'l10n_br_data_account',
        'account_product_fiscal_classification',
    ],
    'data': [
        'l10n_br_account_product_sequence.xml',
        'account_invoice_workflow.xml',
        'data/l10n_br_account_product.cfop.csv',
        'data/l10n_br_account.fiscal.document.csv',
        'data/l10n_br_account_product_data.xml',
        'views/l10n_br_account_product_view.xml',
        'views/l10n_br_account_view.xml',
        'views/l10n_br_account_product_view.xml',
        'views/account_view.xml',
        'views/account_invoice_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/account_product_fiscal_classification_view.xml',
        'views/product_view.xml',
        'wizard/l10n_br_account_nfe_export_invoice_view.xml',
        'wizard/l10n_br_account_nfe_export_view.xml',
        'wizard/l10n_br_account_document_status_sefaz_view.xml',
        'wizard/account_invoice_refund_view.xml',
        'security/l10n_br_account_product_security.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/account_tax_code_demo.xml',
        'demo/account_tax_demo.xml',
        'demo/base_demo.xml',
        'demo/product_demo.xml',
        'demo/l10n_br_account_product_demo.xml',
        'demo/account_fiscal_position_rule_demo.xml',
        'demo/product_taxes.yml',
    ],
    'test': [
        'test/account_customer_invoice.yml',
        'test/account_supplier_invoice.yml',
        'test/account_invoice_refund.yml',
        'test/nfe_export.yml',
    ],
    'installable': True,
    'auto_install': False,
}
