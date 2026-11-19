# Copyright 2026 KMEE INFORMATICA LTDA - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from erpbrasil.assinatura import misc

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


def load_nfe_dfe_fixture_files(env):
    """Load the demo data the l10n_br_nfe_dfe tests rely on as fixtures.

    Odoo 19 installs no demo data by default: the tests need the demo
    companies, the fiscal demo documents and the NF-e demo documents.
    """
    if env.ref("l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False):
        return
    # as the demo data is loaded at install time: as superuser, with the main
    # company active
    main_company = env.ref("base.main_company")
    env = env(su=True, context=dict(env.context, allowed_company_ids=main_company.ids))
    load_fiscal_fixture_files(env)
    _ensure_fake_certificates(env)
    # the companies first: the NF-e fields of the documents are only
    # computed for companies with the OCA processor
    load_fixture_files(
        env,
        "l10n_br_nfe",
        file_names=["company_demo.xml", "fiscal_document_demo.xml"],
    )


def _ensure_fake_certificates(env):
    """Give the demo companies the fake A1 certificate that the
    l10n_br_fiscal_certificate post_init_hook only creates with demo data."""
    for company_xmlid in (
        "base.main_company",
        "l10n_br_base.empresa_simples_nacional",
        "l10n_br_base.empresa_lucro_presumido",
        "l10n_br_base.empresa_lucro_real",
    ):
        company = env.ref(company_xmlid, raise_if_not_found=False)
        if not company or company.certificate_id:
            continue
        company.certificate_id = env["certificate.certificate"].create(
            {
                "scope": "l10n_br",
                "pkcs12_password": "123456",
                "content": misc.create_fake_certificate_file(
                    True,
                    "123456",
                    "EMISSOR A TESTE",
                    "BR",
                    "CERTIFICADO VALIDO TESTE",
                ),
                "company_id": company.id,
            }
        )
