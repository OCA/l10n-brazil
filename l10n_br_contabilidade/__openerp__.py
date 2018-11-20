# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    'name': 'ABGF Contabilidade',
    'category': 'ABGF',
    'license': 'AGPL-3',
    'author': 'ABGF, Odoo Community Association (OCA)',
    'maintainer': 'ABGF',
    'website': 'http://www.abgf.com.br',
    'version': '8.0.0.0.0',
    'depends': [
        'l10n_br_account_product',
        'account_chart_report',
    ],
    'data': [
        'security/ir.model.access.csv',

        'data/natureza_conta_data.xml',
        # Menus
        'views/menu_contabilidade_abgf.xml',
        # Visão
        'views/account_account.xml',
        'views/account_journal.xml',
        'views/account_natureza.xml',
        'views/account_centro_custo.xml',
        'views/account_move.xml',
        'views/account_fechamento.xml',
        'views/account_account_type.xml',
        'views/account_reports.xml',
        'views/account_grupo.xml',
        'views/account_ramo.xml',
        'views/account_historico_padrao.xml',
    ],
    'demo': [
    ],
}
