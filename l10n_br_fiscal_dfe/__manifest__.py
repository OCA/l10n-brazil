# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "L10n BR Fiscal Dfe",
    "summary": """
        Distribuição de documentos fiscais""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "KMEE,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_fiscal"],
    "data": [
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "views/mde/mde_views.xml",
        "views/dfe/dfe_views.xml",
        "views/l10n_br_fiscal_menu.xml",
        "views/res_company_view.xml",
    ],
    "demo": [],
    "external_dependencies": {
        "python": ["erpbrasil.edoc>=2.5.0"],
    },
}
