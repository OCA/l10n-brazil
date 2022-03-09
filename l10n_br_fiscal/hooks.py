# Copyright (C) 2019 - Renato Lima Akretion
# Copyright (C) 2021 - Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import SUPERUSER_ID, _, api, tools

from .constants.fiscal import CERTIFICATE_TYPE_ECNPJ
from .tools import misc

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Import XML data to change core data"""
    env = api.Environment(cr, SUPERUSER_ID, {})

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

    _logger.info(_("Loading l10n_br_fiscal fiscal files. It may take a minute..."))

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
            "demo/fiscal_document_nfse_demo.xml",
            "demo/fiscal_operation_demo.xml",
            "demo/subsequent_operation_demo.xml",
            "demo/l10n_br_fiscal_document_email.xml",
            "demo/res_users_demo.xml",
            "demo/icms_tax_definition_demo.xml",
        ]

        # Load only demo CSV files with few lines instead of thousands
        # unless a flag mention the contrary
        short_files = {
            "load_ncm": "data/l10n_br_fiscal.ncm.csv",
            "load_nbm": "data/l10n_br_fiscal.nbm.csv",
            "load_nbs": "data/l10n_br_fiscal.nbs.csv",
            "load_cest": "data/l10n_br_fiscal.cest.csv",
        }

        for short_file in short_files.keys():
            if tools.config.get(short_file):
                demofiles.append(short_files[short_file])

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

        companies = [
            env.ref("base.main_company", raise_if_not_found=False),
            env.ref("l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False),
            env.ref("l10n_br_base.empresa_simples_nacional", raise_if_not_found=False),
        ]

        for company in companies:
            l10n_br_fiscal_certificate_id = env["l10n_br_fiscal.certificate"]
            company.certificate_nfe_id = l10n_br_fiscal_certificate_id.create(
                misc.prepare_fake_certificate_vals()
            )
            company.certificate_ecnpj_id = l10n_br_fiscal_certificate_id.create(
                misc.prepare_fake_certificate_vals(cert_type=CERTIFICATE_TYPE_ECNPJ)
            )

    if tools.config["without_demo"]:
        prodfiles = []
        # Load full CSV files with few lines unless a flag
        # mention the contrary
        skip_prodfiles = {
            "skip_ncm": "data/l10n_br_fiscal.ncm.csv",
            "skip_nbm": "data/l10n_br_fiscal.nbm.csv",
            "skip_nbs": "data/l10n_br_fiscal.nbs.csv",
            "skip_cest": "data/l10n_br_fiscal.cest.csv",
        }

        for skip_prodfile in skip_prodfiles.keys():
            if not tools.config.get(skip_prodfile):
                prodfiles.append(skip_prodfiles[skip_prodfile])

        _logger.info(
            _(
                "Loading l10n_br_fiscal production files. It may take at least"
                " 3 minutes..."
            )
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

    _logger.info(_("Loading l10n_br_fiscal post init files. It may take a minute..."))

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

    # Load post demo files
    if not tools.config["without_demo"]:
        posdemofiles = [
            "demo/fiscal_document_demo.xml",
        ]

        _logger.info(
            _("Loading l10n_br_fiscal post demo files. It may take a minute...")
        )

        for file in posdemofiles:
            tools.convert_file(
                cr,
                "l10n_br_fiscal",
                file,
                None,
                mode="demo",
                noupdate=True,
                kind="init",
                report=None,
            )

    # Create a fiscal dummy for the company if you don't have one.
    companies = env["res.company"].search([("fiscal_dummy_id", "=", False)])
    for c in companies:
        c.write(
            {
                "fiscal_dummy_id": c._default_fiscal_dummy_id().id,
            }
        )
