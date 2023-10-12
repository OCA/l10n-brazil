# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Banco Inter - Integração com a API",
    "summary": """
        Integração com a API do Banco Inter""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "maintainers": ["mileo", "ygcarvalh"],
    "development_status": "Alpha",
    "depends": [
        "l10n_br_account_payment_order",
    ],
    "data": [
        "views/account_move.xml",
        "views/account_move_line.xml",
        "views/account_journal.xml",
    ],
    "demo": [
        "demo/res_partner_bank.xml",
        "demo/ir_sequence.xml",
        "demo/account_journal.xml",
        "demo/account_payment_mode.xml",
        "demo/account_invoice.xml",
    ],
    "external_dependencies": {
        "python": [
            "erpbrasil.bank.inter",
        ]
    },
}
