# -*- coding: utf-8 -*-
# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian - Generic Accounting',
    'category': 'Localization',
    'summary': """
Base module for the Brazilian localization
==========================================

This module consists in:

 - Generic Brazilian chart of accounts
 - Brazilian taxes such as:

        - IPI
        - ICMS
        - PIS
        - COFINS
        - ISS
        - IR
        - IRPJ
        - CSLL

The field tax_discount has also been added in the account.tax.template and
account.tax objects to allow the proper computation of some Brazilian VATs
such as ICMS. The chart of account creation wizard has been extended to
propagate those new data properly.
""",
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoobrasil.org',
    'version': '10.0.1.0.0',
    'depends': ['account'],
    'data': [
        'data/account_tax_group_data.xml',
        'data/l10n_br_chart_data.xml',
        'data/account.account.template.csv',
        'data/account_tax_template_data.xml',
        'views/account_view.xml',
        'data/account_chart_template_data.yml',
    ],
}
