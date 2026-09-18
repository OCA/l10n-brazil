{
    "name": "NFS-e Nacional",
    "summary": "Brazilian Electronic Invoice for Services (National Standard)",
    "version": "16.0.1.1.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "external_dependencies": {
        "python": [
            "nfelib",
            "erpbrasil.assinatura",
            "requests",
            "cryptography",
        ],
    },
    "depends": [
        "l10n_br_nfse",
        "l10n_br_nfse_spec",
        "spec_driven_model",
    ],
    "data": [
        "wizards/document_cancel_wizard.xml",
        "views/document_view.xml",
        "report/danfse_nacional.xml",
    ],
    "demo": [
        "demo/fiscal_document_demo.xml",
    ],
    "installable": True,
    "auto_install": False,
}
