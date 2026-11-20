{
    "name": "NFS-e Nacional",
    "summary": "Brazilian Electronic Invoice for Services (National Standard)",
    "version": "16.0.1.2.1",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "Akretion, KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "external_dependencies": {
        "python": [
            # The NFS-e NT 009 (leiaute 1.04.01) bindings first shipped in
            # nfelib 3.3.0: finNFSe moved to infDPS and
            # TcrtcinfoTributosIbscbs became TcrtcinfoTribIbscbs.
            "nfelib>=3.3.0",
            "brazilfiscalreport",
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
