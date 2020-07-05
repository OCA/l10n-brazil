# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Financial',
    'summary': """
        Contas a Pagar e a Receber""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://www.kmee.com.br',
    'depends': [
        'l10n_br_account',
        'l10n_br_resource',
        'account_payment_mode',
        'account_financial_report',
        'report_xlsx',
    ],
    'data': [
        'security/account_payment.xml',

        'views/financial_menu.xml',

        'wizards/financial_cancel.xml',
        # 'wizards/financial_edit.xml',
        # 'wizards/financial_pay_receive.xml',
        'wizards/report_xlsx_financial_cashflow_wizard_view.xml',
        'wizards/report_xlsx_financial_moves_states_wizard.xml',
        'wizards/report_xlsx_financial_defaults_wizard.xml',
        'wizards/report_xlsx_financial_partner_statement_wizard.xml',

        'views/account_payment_base_view.xml',
        'views/account_payment_2receive_view.xml',
        'views/account_payment_debt_2pay_view.xml',
        'views/financial_account_view.xml',
        'views/fiscal_operation_view.xml',

        'views/document.xml',

        'reports/report_xlsx_financial_cashflow_data.xml',
        'reports/report_xlsx_financial_moves_states_data.xml',
        'reports/report_xlsx_financial_defaults_data.xml',
        'reports/report_xlsx_financial_partner_statement_data.xml',
    ],
    'demo': [
        'demo/financial.account.csv',
    ],
}
