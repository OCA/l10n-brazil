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
        'account_payment_mode',
    ],
    'data': [
        # 'security/account_payment.xml',

        'views/financial_menu.xml',

        'views/account_payment_base_view.xml',
        'views/account_payment_2receive_view.xml',
        'views/account_payment_debt_2pay_view.xml',

        'views/document.xml',
    ],
    'demo': [
        # 'demo/account_payment.xml',
    ],
}
