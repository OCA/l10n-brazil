# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    'name': 'Contabilidade Brasileira',
    'category': 'ABGF',
    'license': 'AGPL-3',
    'author': 'ABGF, Odoo Community Association (OCA)',
    'maintainer': 'ABGF',
    'website': 'http://www.abgf.com.br',
    'version': '8.0.0.0.0',
    'depends': [
        'l10n_br_account_product',
        'account_financial_report_webkit',
        'account_chart_report',
        'account_financial_report_webkit',
        'mis_builder',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'security/account_groups.xml',
        #
        'data/natureza_conta_data.xml',
        # # Menus
        'views/menu_l10n_br_contabilidade.xml',
        # # Relatórios
        'reports/report.xml',

        # Wizard
        'wizards/fechamento_reabertura_justificativa_wizard.xml',
        'wizards/periodo_reabertura_justificativa_wizard.xml',
        'wizards/trial_balance_wizard.xml',
        'wizards/general_ledger_wizard.xml',
        'wizards/import_account_account.xml',
        'wizards/import_account_depara.xml',
        'wizards/print_journal_wizard.xml',
        'wizards/verification_account_depara.xml',

        'views/account_account.xml',
        'views/account_journal.xml',
        'views/account_natureza.xml',
        'views/account_centro_custo.xml',
        'views/account_move.xml',
        'views/account_fechamento.xml',
        'views/account_fechamento_reabertura_justificativa.xml',
        'views/account_reabertura_periodo_justificativa.xml',
        'views/account_account_type.xml',
        'views/account_reports.xml',  # já presente no meu account.final_accounting_reports
        'views/account_grupo.xml',
        'views/account_ramo.xml',
        'views/account_period.xml',
        'views/account_historico_padrao.xml',
        'views/account_depara.xml',
        'views/account_depara_plano.xml',
        'views/mis_report.xml',
        'views/mis_report_instance.xml',
        'views/mis_report_kpi.xml',
        'views/mis_report_style.xml',
        'views/account_fiscalyear.xml',
        'views/res_partner.xml',
        'views/account_event.xml',
        'views/account_event_line.xml',
        'views/account_event_template.xml',
        'views/account_invoice.xml',
        'views/l10n_br_account.xml',
        'views/account_product.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'demo': [
    ],
}
