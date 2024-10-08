# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "CT-e",
    "summary": """Brazilian Electronic Invoice CT-e""",
    "version": "14.0.1.0.0",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_fiscal_edi",
        "l10n_br_cte_spec",
        "l10n_br_fiscal_certificate",
        "spec_driven_model",
    ],
    "data": [
        "security/ir.model.access.csv",
        # "views/document_line.xml",
        # 'views/document_related.xml',
        # 'views/res_partner.xml',
        "modal/modal_rodoviario.xml",
        "modal/modal_aquaviario.xml",
        "modal/modal_ferroviario.xml",
        "modal/modal_aereo.xml",
        "views/res_company.xml",
        "views/cte_document.xml",
        "wizards/document_correction_wizard.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
    "external_dependencies": {
        "python": [
            "nfelib<=2.0.7",
            "erpbrasil.assinatura>=1.7.0",
            "erpbrasil.transmissao>=1.1.0",
            "erpbrasil.edoc>=2.5.2",
        ],
    },
}
