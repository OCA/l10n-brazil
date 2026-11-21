# Copyright 2018 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "SPED - EFD PIS COFINS",
    "summary": """
        Registros do EFD PIS COFINS do SPED""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "maintainers": ["rvalyi", "renatonlima"],
    "depends": [
        "l10n_br_sped_base",
        "l10n_br_account",
        "l10n_br_tax_assessment",
    ],
    "external_dependencies": {
        "python": [
            "erpbrasil-base>=2.4.2",
        ]
    },
    "data": [
        "security/ir.model.access.csv",
        "security/credit_opening_security.xml",
        "views/sped_efd_pis_cofins.xml",
        "views/credit_opening_views.xml",
        "views/tax_assessment_views.xml",
    ],
    "demo": ["demo/efd_pis_cofins_demo.xml"],
    "application": True,
    "post_init_hook": "post_init_hook",
}
