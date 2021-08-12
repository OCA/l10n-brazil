# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Payent Cielo',
    'summary': """
        Payment Acquirer: Cielo Implementation""",
    'version': '12.0.3.2.1',
    "development_status": "Alpha",
    'license': 'AGPL-3',
    'author': 'KMEE INFORMATICA LTDA,Odoo Community Association (OCA)',
    'maintainers': ['DiegoParadeda'],
    'website': 'https://github.com/OCA/l10n-brazil',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_cielo_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',
}
