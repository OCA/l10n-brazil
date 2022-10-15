# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>

{
    "name": "Account Payment Way",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Engenere," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "14.0.0.0.1",
    "development_status": "Alpha",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "data/account_payment_way.xml",
        "views/account_move_view.xml",
        "views/account_move_line_view.xml",
        "views/account_base_menu.xml",
    ],
    "installable": True,
}
