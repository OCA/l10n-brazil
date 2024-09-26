# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e (FocusNFE)",
    "summary": """
        NFS-e (FocusNFE)""",
    "version": "14.0.1.2.1",
    "license": "AGPL-3",
    "author": "KMEE, Escodoo, Odoo Community Association (OCA)",
    "maintainers": [
        "AndreMarcos",
        "mileo",
        "ygcarvalh",
        "marcelsavegnago",
    ],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "depends": [
        "l10n_br_nfse",
    ],
    "data": [
        "views/res_company.xml",
        "data/l10n_br_nfse_focus_cron.xml",
    ],
}
