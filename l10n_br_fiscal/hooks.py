# Copyright (C) 2019 - Renato Lima Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, tools

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Import XML data to change core data"""

    files = [
        "data/l10n_br_fiscal.cnae.csv",
        "data/l10n_br_fiscal.cfop.csv",
        "data/l10n_br_fiscal_cfop_data.xml",
        "data/l10n_br_fiscal.tax.ipi.control.seal.csv",
        "data/l10n_br_fiscal.tax.ipi.guideline.csv",
        "data/l10n_br_fiscal.tax.ipi.guideline.class.csv",
        "data/l10n_br_fiscal.tax.pis.cofins.base.csv",
        "data/l10n_br_fiscal.tax.pis.cofins.credit.csv",
        "data/l10n_br_fiscal.service.type.csv",
        "data/simplified_tax_data.xml",
        "data/operation_data.xml",
        "data/l10n_br_fiscal_tax_icms_data.xml",
    ]

    _logger.info(
        _("Loading l10n_br_fiscal fiscal files. It may take a minute..."))

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

    if not tools.config["without_demo"]:
        demofiles = [
            "demo/l10n_br_fiscal.ncm-demo.csv",
            "demo/l10n_br_fiscal.nbm-demo.csv",
            "demo/l10n_br_fiscal.nbs-demo.csv",
            "demo/l10n_br_fiscal.cest-demo.csv",
            "demo/city_taxation_code_demo.xml",
            "demo/company_demo.xml",
            "demo/product_demo.xml",
            "demo/partner_demo.xml",
            "demo/fiscal_document_demo.xml",
            "demo/fiscal_operation_demo.xml",
            "demo/subsequent_operation_demo.xml",
            "demo/l10n_br_fiscal_document_email.xml",
            "demo/fiscal_document_nfse_demo.xml",
            "demo/res_users_demo.xml",
        ]

        # Load only demo CSV files with few lines instead of thousands
        # unless a flag mention the contrary
        if tools.config.get("load_ncm"):
            demofiles.append("data/l10n_br_fiscal.ncm.csv")

        if tools.config.get("load_nbm"):
            demofiles.append("data/l10n_br_fiscal.nbm.csv")

        if tools.config.get("load_nbs"):
            demofiles.append("data/l10n_br_fiscal.nbs.csv")

        if not tools.config.get("load_cest"):
            demofiles.append("data/l10n_br_fiscal.cest.csv")

        _logger.info(_("Loading l10n_br_fiscal demo files."))

        for f in demofiles:
            tools.convert_file(
                cr,
                "l10n_br_fiscal",
                f,
                None,
                mode="init",
                noupdate=True,
                kind="demo",
                report=None,
            )

    elif tools.config["without_demo"]:
        prodfiles = []
        # Load full CSV files with few lines unless a flag
        # mention the contrary
        if not tools.config.get("skip_ncm"):
            prodfiles.append("data/l10n_br_fiscal.ncm.csv")

        if not tools.config.get("skip_nbm"):
            prodfiles.append("data/l10n_br_fiscal.nbm.csv")

        if not tools.config.get("skip_nbs"):
            prodfiles.append("data/l10n_br_fiscal.nbs.csv")

        if not tools.config.get("skip_cest"):
            prodfiles.append("data/l10n_br_fiscal.cest.csv")

        _logger.info(_(
            "Loading l10n_br_fiscal production files. It may take at least"
            " 3 minutes...")
        )

        for f in prodfiles:
            tools.convert_file(
                cr,
                "l10n_br_fiscal",
                f,
                None,
                mode="init",
                noupdate=True,
                kind="init",
                report=None,
            )

    # Load post files
    posloadfiles = [
        "data/l10n_br_fiscal_icms_tax_definition_data.xml",
    ]

    _logger.info(
        _("Loading l10n_br_fiscal post init files. It may take a minute...")
    )

    for file in posloadfiles:
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
