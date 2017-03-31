# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Financial Account',
    'summary': """
        Integrate financial module with Odoo accounting""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'financial',
        'account',
    ],
    'data': [
        'views/account_invoice.xml',
        'views/account_journal.xml',
        'views/account_move.xml',
        'views/financial_move.xml',
    ],
    'demo': [
    ],
}
