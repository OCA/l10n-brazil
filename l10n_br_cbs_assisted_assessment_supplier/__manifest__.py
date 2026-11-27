# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Brazilian CBS Assisted Assessment Suppliers",
    "summary": "Read-only CBS supplier board from assessment credits and RAD",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo, Odoo Community Association (OCA)",
    "maintainers": ["marcelsavegnago"],
    "website": "https://github.com/OCA/l10n-brazil",
    "category": "Accounting",
    "development_status": "Alpha",
    "depends": [
        "l10n_br_cbs_assisted_assessment",
    ],
    "data": [
        "security/supplier_security.xml",
        "security/ir.model.access.csv",
        "views/supplier_view.xml",
        "views/assisted_assessment_view.xml",
    ],
    "installable": True,
}
