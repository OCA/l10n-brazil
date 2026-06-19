# Copyright 2026 - TODAY, Akretion
# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "NFS-e Nacional (Padrão Nacional SEFIN)",
    "summary": "NFS-e Nacional - Direct integration with SEFIN REST API",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion, Escodoo, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "external_dependencies": {
        "python": [
            "nfelib",
            "erpbrasil.assinatura",
            "requests",
            "cryptography",
            "brazilfiscalreport",
            "qrcode",
        ],
    },
    "depends": [
        "l10n_br_nfse",
        "l10n_br_nfse_spec",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_company_view.xml",
        "views/document_view.xml",
        "views/document_line_view.xml",
        "wizards/document_import_nfse_wizard.xml",
        "data/nfse_nacional_cron.xml",
    ],
}
