# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Cnab Erpbrasil Febraban',
    'summary': """
        Integração com CNAB através da biblioteca erpbrasil.febraban""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'depends': [
        'l10n_br_account_payment_order',
    ],
    'data': [
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': [
            'febraban',
        ],
    },
}
