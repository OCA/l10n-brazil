# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Financial',
    'summary': """
        Financeiro brasileiro (Tesouraria e Integracao Bancaria)""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.odoobrasil.org.br',
    'depends': [
        'financial',
    ],
    'data': [
        'security/financeiro_tipo_documento.xml',
        'views/financeiro_tipo_documento.xml',
        'views/financial_move.xml',
        'security/financeiro_cheque.xml',
        'views/financeiro_cheque.xml',
        'security/account_payment_mode.xml',
        'views/account_payment_mode.xml',
        'security/account_payment_method.xml',
        'views/account_payment_method.xml',
    ],
    'demo': [
        'demo/financeiro_tipo_documento.xml',
        'demo/financeiro_cheque.xml',
        'demo/account_payment_mode.xml',
        'demo/account_payment_method.xml',
    ],
    'installable': False,
}
