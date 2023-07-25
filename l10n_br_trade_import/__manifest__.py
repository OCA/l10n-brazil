# Copyright (C) 2023-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Import Declaration Management",
    "summary": "Managing Brazilian Import Declarations",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Engenere," "Odoo Community Association (OCA)",
    "maintainers": ["antoniospneto", "felipemotter"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "14.0.0.0.0",
    "development_status": "Beta",
    "depends": [
        "l10n_br_nfe",
        "l10n_br_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/import_declaration.xml",
        "views/import_addition.xml",
        "views/account_move_views.xml",
        "views/nfe_adi_view.xml",
        "views/nfe_di_view.xml",
        "views/nfe_document_view.xml",
    ],
    "installable": True,
}
