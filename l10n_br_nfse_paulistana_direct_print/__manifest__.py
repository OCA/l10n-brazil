# Copyright (C) 2023 Antônio S. P. Neto <neto@engene.one> - Engenere LTDA
#     (https://engenere.one).
# Copyright (C) 2023 Marcel Savegnago <marcel.savegnago@escodoo.com.br> - Escodoo
#     (https://www.escodoo.com.br).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Direct print of Paulistana NFS-e",
    "summary": """
        Print the NFS-e directly from the São Paulo municipality website""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Engenere, Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["antoniospneto", "marcelsavegnago"],
    "development_status": "Beta",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": [
        "l10n_br_nfse_paulistana",
        "l10n_br_account",
    ],
    "data": [
        "views/document_view.xml",
    ],
}
