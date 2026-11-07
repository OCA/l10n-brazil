# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian Localization Sale Rental",
    "summary": "Locação de bens móveis (sale_rental) com remessa e retorno em NF-e"
    " e fatura do aluguel em NFS-e",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "maintainers": ["mileo"],
    "depends": [
        "sale_rental",
        "l10n_br_sale_stock",
    ],
    "data": [
        "views/res_company_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
