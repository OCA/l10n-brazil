# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{
    'name': 'Account Payment CNAB',
    'version': '10.0.1.0.0',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'http://www.kmee.com.br',
    'external_dependencies': {
        'python': ['cnab240',
                   'pyboleto'],
    },
    'depends': [
        'base_transaction_id',
        'l10n_br_account_payment_order',
    ],
    'data': [
        'security/cnab_cobranca_security.xml',
        'views/l10n_br_payment_cnab.xml',
        'views/payment_order.xml',
        'views/l10n_br_cnab_sequence.xml',
        'views/l10n_br_cobranca_cnab.xml',
        'views/l10n_br_cobranca_cnab_lines.xml',
        'views/account_move_line.xml',
        'views/res_partner_bank.xml',
        'views/l10n_br_cnab_retorno_view.xml',
        'views/payment_mode.xml',
        'views/payment_line.xml',
        'views/bank_payment_line.xml',
        'data/l10n_br_payment_export_type.xml',
        # 'data/l10n_br_payment_mode.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        # 'demo/l10n_br_payment_mode.xml',
    ],
    'test': [
        # 'tests/invoice_create.yml'
    ],
    "installable": True,
    "auto_install": False,
}
