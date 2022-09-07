# Copyright 2018 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Br Pos Cfe",
    "summary": """CF-e""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Point Of Sale",
    "development_status": "Alpha",
    "maintainers": ["mileo", "sadamo", "gabrielcardoso21", "lfdivino"],
    "depends": [
        "point_of_sale",
        "l10n_br_pos",
    ],
    "external_dependencies": {
        "python": ["satcomum"],
    },
    "data": [
        # Views
        "views/pos_payment_method_view.xml",
        # Templates
        "views/pos_template.xml",
    ],
    "demo": [],
    "installable": True,
}
