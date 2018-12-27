# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    'name': 'L10nBR Contabilidade',
    'category': 'ABGF',
    'license': 'AGPL-3',
    'author': 'ABGF, Odoo Community Association (OCA)',
    'maintainer': 'ABGF',
    'website': 'http://www.abgf.com.br',
    'version': '8.0.0.0.0',
    'depends': [
        'l10n_br_account_product',
        'account_chart_report',
        'account_financial_report_webkit',
        'mis_builder',
    ],
    'data': [
        'views/menu_l10n_br_contabilidade.xml',
        # 'security/ir.model.access.csv',
        #
        # 'data/natureza_conta_data.xml',
        # # Menus
        # 'views/menu_contabilidade_abgf.xml',
        # # Relatórios
        # 'reports/report.xml',
        # # Visão
        # 'wizards/fechamento_reabertura_justificativa_wizard.xml',
        # 'wizards/trial_balance_wizard.xml',
        # 'views/account_account.xml',
        # 'views/account_account_report.xml',
        # 'views/account_account_report_line.xml',
        # 'views/account_journal.xml',
        # 'views/account_natureza.xml',
        # 'views/account_centro_custo.xml',
        # 'views/account_move.xml',
        # 'views/account_fechamento.xml',
        # 'views/account_fechamento_reabertura_justificativa.xml',
        # 'views/account_fiscalyear.xml',
        # 'views/account_account_type.xml',
        # 'views/account_reports.xml',
        'views/account_grupo.xml',
        'views/account_ramo.xml',
        # 'views/account_period.xml',
        'views/account_historico_padrao.xml',
        # 'views/account_mapeamento.xml',
        # 'views/account_saldo.xml',
    ],
    'demo': [
    ],
}
