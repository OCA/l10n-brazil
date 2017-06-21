# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

{
    'name': u'SPED - Account',
    'version': '10.0.1.0.0',
    'author': u'"Odoo Community Association (OCA), Ari Caldeira',
    'category': u'Base',
    'depends': [
        'sped',
        'account',
        'sped_imposto',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'data': [
        'data/inherited_account_account_type_dre_data.xml',
        'data/inherited_account_account_type_balanco_data.xml',
        'data/inherited_account_financial_report_dre_data.xml',
        'data/inherited_account_financial_report_balanco_data.xml',
        'data/inherited_account_chart_template_data.xml',
        'data/inherited_account_chart_template_data.xml',
        'data/inherited_account_account_template_data.xml',
        'data/inherited_account_chart_template_properties_data.xml',

        'views/inherited_account_account_type_view.xml',
        'views/inherited_account_account_template_view.xml',
        'views/inherited_account_account_view.xml',
        'views/inherited_account_bank_statement_view.xml',
        'views/inherited_account_config_settings_view.xml',
        'views/account_invoice_line_brazil_view.xml',
        'views/inherited_account_invoice_customer_view.xml',
        'views/inherited_account_invoice_supplier_view.xml',
        'views/inherited_account_journal_view.xml',
        'views/inherited_account_move_view.xml',
        'views/inherited_account_move_line_view.xml',
        'views/inherited_account_financial_report_view.xml',
        'views/sped_account_move_template_view.xml',
        'views/inherited_sped_documento_base_view.xml',
        'views/inherited_sped_operacao_base_view.xml',
    ],
}
