# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "NFS-e Received Documents Import",
    "summary": (
        "Fetch received NFS-e as tomador via NFS-e Nacional "
        "(SEFAZ ADN REST with e-CNPJ mTLS), with cron-based sync and a review "
        "step before creating a vendor bill (account.move)."
    ),
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Localisation",
    "depends": [
        "l10n_br_nfse",
        "l10n_br_fiscal_certificate",
        "l10n_br_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/nfse_received_views.xml",
        "views/nfse_dfe_views.xml",
        "views/menu.xml",
        "wizards/nfse_import_wizard.xml",
    ],
    "external_dependencies": {
        "python": ["lxml", "requests", "cryptography"],
    },
    "installable": True,
    "auto_install": False,
}
