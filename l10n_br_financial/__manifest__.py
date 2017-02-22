# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Financial',
    'summary': """
        Financial""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'mail',
        'account_payment_mode'
        'l10n_br_resource',
        'l10n_br_account',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'views/financial_menu.xml',
        'security/financial_move_model.xml',
        'wizards/financial_create.xml',
        'wizards/financial_renegociate.xml',
        'wizards/financial_edit.xml',
        'wizards/financial_pay_receive.xml',
        'wizards/financial_cancel.xml',
        'security/financial_move.xml',
        'views/financial_move.xml',
    ],
    'demo': [
        'demo/financial_move_history.xml',
        'demo/financial_move.xml',
    ],
}
