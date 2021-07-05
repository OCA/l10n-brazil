# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Banco Inter - Integração com a API',
    'summary': """
        Integração com a API do Banco Inter""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://github.com/oca/l10n-brazil.git',
    'maintainers': ['mileo'],
    'development_status': 'Alpha',
    'depends': [
        'l10n_br_account_payment_order',
    ],
    'data': [
        'views/account_invoice.xml',
        'views/account_move_line.xml',
        'views/account_journal.xml',

        'data/cron.xml',
    ],
    'demo': [
        'demo/res_partner_bank.xml',
        'demo/ir_sequence.xml',
        'demo/account_journal.xml',
        'demo/account_payment_mode.xml',
        'demo/account_invoice.xml',
        'demo/account_payment_order.xml',
    ],
    "external_dependencies": {"python": [
        "erpbrasil.bank.inter",
    ]},
}
