{
    "name": "SPED EFD - ICMS IPI",
    "version": "14.0.1.0.0",
    "author": "KMEE, Odoo Community Association (OCA)",
    "websitie": "https://github.com/OCA/l10n-brazil",
    "category": "Base",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_fiscal_closing",
    ],
    "installable": True,
    "data": [
        "security/ir.model.access.csv",
        "views/efd_icms_ipi_view.xml",
    ],
    "external_dependencies": {
        "python": [
            "email_validator",
            "python-sped",
        ],
    },
}
