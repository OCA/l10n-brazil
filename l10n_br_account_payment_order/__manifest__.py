# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Payment Order",
    "version": "14.0.7.0.0",
    "license": "AGPL-3",
    "author": "KMEE, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["mbcosta"],
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Banking addons",
    "depends": [
        "l10n_br_base",
        "account_payment_order",
        "l10n_br_account_due_list",
        "account_due_list_payment_mode",
    ],
    "data": [
        # Security
        "security/cnab_cobranca_security.xml",
        "security/ir.model.access.csv",
        # Data
        "data/cnab_data.xml",
        "data/l10n_br_payment_export_type.xml",
        "data/boleto_data.xml",
        # CNAB Mov. Instruction and Return Codes
        "data/cnab_codes/banco_bradesco_cnab_240_400.xml",
        "data/cnab_codes/banco_cef_cnab_240.xml",
        "data/cnab_codes/banco_do_brasil_cnab_400.xml",
        "data/cnab_codes/banco_itau_cnab_240_400.xml",
        "data/cnab_codes/banco_sicred_cnab_240.xml",
        "data/cnab_codes/banco_unicred_cnab_240_400.xml",
        "data/cnab_codes/banco_ailos_cnab_240.xml",
        "data/cnab_codes/banco_santander_cnab_240_400.xml",
        # Boleto Wallet Code
        "data/cnab_codes/banco_santander_boleto_wallet_code.xml",
        "data/cnab_codes/banco_bradesco_boleto_wallet_code.xml",
        # Wizards
        "wizards/account_payment_line_create_view.xml",
        "wizards/account_move_line_change.xml",
        # Views
        "views/account_journal.xml",
        "views/account_payment_order.xml",
        "views/account_payment_line.xml",
        "views/account_payment_mode.xml",
        "views/l10n_br_cnab_return_log_view.xml",
        "views/account_move_line.xml",
        "views/l10n_br_cnab_return_move_code_view.xml",
        "views/account_payment_views.xml",
        "views/l10n_br_cnab_mov_instruction_code_view.xml",
        "views/account_move_view.xml",
        "views/l10n_br_cnab_boleto_wallet_code_view.xml",
        # Códigos CNAB
        "views/l10n_br_cnab_code_view.xml",
        "views/l10n_br_cnab_config_view.xml",
    ],
    "demo": [
        "demo/account_payment_method.xml",
        "demo/mov_instruction_code.xml",
        "demo/res_partner_bank.xml",
        "demo/account_account.xml",
        "demo/account_journal.xml",
        "demo/ir_sequence.xml",
        "demo/l10n_br_cnab_config_demo.xml",
        "demo/account_payment_mode.xml",
        "demo/account_invoice.xml",
        "demo/res_users.xml",
        "demo/account_payment_order.xml",
    ],
    "installable": True,
    "external_dependencies": {
        "python": [
            "erpbrasil.base>=2.3.0",
        ]
    },
}
