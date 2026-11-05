# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account NFS-e Integration",
    "summary": "Integration between l10n_br_account and l10n_br_nfse: NFS-e "
    "of invoices in foreign currency is issued in reais",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "depends": [
        "l10n_br_account",
        "l10n_br_nfse",
    ],
    "auto_install": True,
    "installable": True,
}
