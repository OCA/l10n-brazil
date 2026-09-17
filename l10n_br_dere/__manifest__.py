# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian DeRE",
    "summary": "Specific-regime declaration: tables, trial balance and monthly closing",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Accounting",
    "development_status": "Beta",
    "depends": [
        "l10n_br_account",
        "l10n_br_base",
        "l10n_br_coa",
        "l10n_br_dere_spec",
        "l10n_br_fiscal",
        "l10n_br_fiscal_certificate",
        "mail",
    ],
    "data": [
        "security/dere_security.xml",
        "security/ir.model.access.csv",
        "data/l10n_br_dere.activity.csv",
        "data/l10n_br_dere.tax.code.csv",
        "data/ir_cron.xml",
        "views/res_company_view.xml",
        "views/account_account_view.xml",
        "views/fiscal_operation_view.xml",
        "views/dere_activity_view.xml",
        "views/dere_tax_code_view.xml",
        "views/dere_reserve_asset_view.xml",
        "views/dere_declaration_view.xml",
        "views/dere_event_view.xml",
        "views/dere_pgcc_account_view.xml",
        "views/dere_menu.xml",
    ],
    "demo": [
        "demo/dere_demo.xml",
    ],
    "installable": True,
    "application": False,
    "external_dependencies": {
        "python": [
            "erpbrasil.assinatura",
            "lxml",
            "requests",
            "signxml",
        ]
    },
}
