# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Payment Pagseguro',
    'summary': """
        Pagseguro""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/l10n-brazil.git',
    'depends': [
        'payment',
    ],
    'data': [
        'views/payment_pagseguro_templates.xml',

        'data/payment_acquirer_data.xml',
        'views/payment_acquirer.xml',
    ],
    'demo': [
    ],
}
