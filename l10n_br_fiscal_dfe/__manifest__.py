# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "L10n BR Fiscal Dfe",
    "summary": """
        Distribuição de documentos fiscais""",
    "version": "16.0.1.0.2",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_fiscal", "l10n_br_fiscal_certificate"],
    "data": [
        # Data
        "data/ir_cron.xml",
        # Security
        "security/dfe_security.xml",
        "security/ir.model.access.csv",
        # Views
        "views/dfe/dfe_monitor_views.xml",
        "views/dfe/dfe_views.xml",
        "views/dfe/dfe_access_key.xml",
        "views/l10n_br_fiscal_menu.xml",
        "views/res_company_view.xml",
    ],
    "external_dependencies": {
        "python": [
            "erpbrasil.edoc>=2.5.2",
            "erpbrasil.transmissao>=1.1.0",
            "nfelib<=2.0.7",
        ],
    },
}
