# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# Copyright (C) 2022-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account NFe/NFC-e Integration",
    "summary": "Integration between l10n_br_account and l10n_br_nfe",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Engenere," "Akretion," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "12.0.1.1.0",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_nfe",
        "l10n_br_account",
        "account_payment_partner",
    ],
    "data": [
        "views/account_payment_mode.xml",
    ],
    "demo": [
        "demo/account_invoice_demo.xml",
    ],
    "installable": True,
    "auto_install": True,
}
