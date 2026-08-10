# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Apuração de Impostos sobre Consumo (Brasil)",
    "summary": "Conta gráfica mensal de ICMS, IPI, PIS e COFINS",
    "version": "16.0.1.0.0",
    "category": "Localization/Brazil",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Beta",
    "maintainers": ["mileo"],
    "depends": [
        "l10n_br_account",
        "account_tax_balance",
    ],
    "data": [
        "security/tax_assessment_security.xml",
        "security/ir.model.access.csv",
        "views/tax_assessment_views.xml",
    ],
    "demo": [
        "demo/tax_assessment_demo.xml",
    ],
    "installable": True,
}
