# Copyright 2018 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

{
    "name": "SPED Base",
    "summary": """
        Framework abstrato pro SPED""",
    "version": "18.0.1.6.2",
    "license": "AGPL-3",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-brazil",
    "depends": ["l10n_br_fiscal_edi"],
    "maintainers": ["rvalyi"],
    "development_status": "Alpha",
    "demo": ["demo/sped_base_demo.xml"],
    "data": [
        "security/ir.model.access.csv",
        "views/sped_base.xml",
        "views/res_partner_view.xml",
        "views/sped_signer_view.xml",
        "views/res_company_view.xml",
    ],
}
