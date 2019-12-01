# Copyright 2019 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Account Nfe',
    'summary': """
        Main NF'e (Brazilian Electronic Invoicing) module. It makes the bridge between the account and the l10n_br_nfe modules.""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Akretion,Odoo Community Association (OCA)',
    'depends': [
        'l10n_br_nfe',
        'l10n_br_account'
    ],
    'data': [
    ],
    'demo': [
    ],
    'post_init_hook': 'post_init_hook',
}
