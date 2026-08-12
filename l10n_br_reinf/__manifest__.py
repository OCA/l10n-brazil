# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "EFD-Reinf",
    "summary": "EFD-Reinf: withholding and other fiscal information for Brazil",
    "category": "Localisation",
    "license": "AGPL-3",
    "author": "KMEE, Odoo Community Association (OCA)",
    "maintainers": ["mileo"],
    "website": "https://github.com/OCA/l10n-brazil",
    "development_status": "Alpha",
    "version": "16.0.1.0.0",
    "depends": [
        "l10n_br_reinf_spec",
        "spec_driven_model",
        "l10n_br_fiscal_edi",
        "l10n_br_account_withholding",
        "l10n_br_fiscal_certificate",
        "l10n_br_resource",
    ],
    "external_dependencies": {"python": ["nfelib"]},
    "data": [
        # Security
        "security/ir.model.access.csv",
        "security/reinf_security.xml",
        # Data
        "data/ir_sequence.xml",
        # The parent table comes before the mapping that points at it.
        "data/l10n_br_reinf.revenue.code.csv",
        "data/l10n_br_reinf.nature.income.csv",
        "data/l10n_br_reinf.nature.income.tax.csv",
        # Views
        "views/reinf_nature_income_view.xml",
        "views/reinf_revenue_code_view.xml",
        "views/reinf_occurrence_view.xml",
        "views/reinf_calculation_view.xml",
        "views/reinf_r1000_view.xml",
        "views/reinf_event_view.xml",
        "views/reinf_batch_view.xml",
        "views/res_company_view.xml",
        "views/reinf_menu.xml",
    ],
    "installable": True,
    "application": False,
}
