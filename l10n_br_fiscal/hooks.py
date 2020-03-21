# Copyright (C) 2019 - Renato Lima Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import tools


def post_init_hook(cr, registry):
    """Import XML data to change core data"""

    files = [
        "data/l10n_br_fiscal.cnae.csv",
        "data/l10n_br_fiscal.cfop.csv",
        "data/l10n_br_fiscal_cfop_data.xml",
        "data/l10n_br_fiscal.tax.ipi.control.seal.csv",
        "data/l10n_br_fiscal.tax.ipi.guideline.csv",
        "data/l10n_br_fiscal.tax.ipi.guideline.class.csv",
        "data/l10n_br_fiscal.ncm.csv",
        "data/l10n_br_fiscal.cest.csv",
        "data/l10n_br_fiscal.tax.pis.cofins.base.csv",
        "data/l10n_br_fiscal.tax.pis.cofins.credit.csv",
        "data/l10n_br_fiscal.nbs.csv",
        "data/l10n_br_fiscal.service.type.csv",
        "data/simplified_tax_data.xml",
        "data/operation_data.xml",
        "data/l10n_br_fiscal_tax_icms_data.xml",
    ]

    for file in files:
        tools.convert_file(
            cr,
            "l10n_br_fiscal",
            file,
            None,
            mode="init",
            noupdate=True,
            kind="init",
            report=None,
        )

    if not tools.config['without_demo']:
        demofiles = [
            "demo/company_demo.xml",
            "demo/product_demo.xml",
            "demo/partner_demo.xml",
            "demo/fiscal_document_demo.xml",
            "demo/fiscal_operation_demo.xml",
        ]

        for f in demofiles:
            tools.convert_file(
                cr,
                "l10n_br_fiscal",
                f,
                None,
                mode="init",
                noupdate=False,
                kind="demo",
                report=None,
            )
