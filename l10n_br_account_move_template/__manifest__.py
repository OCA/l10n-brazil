# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Account Move Template',
    'summary': """
        Modulo temporario pra facilitar o desenvolvimento dos roteiros contabeis""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'l10n_br_account',
        # 'sped'
    ],
    'data': [
        'views/account_move_template_view.xml',
        'views/res_config_view.xml',
        #'data/account.move.template.csv', # TODO exportar dados
    ],
    'demo': [
    ],
}
