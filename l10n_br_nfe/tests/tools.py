# Copyright 2026 KMEE INFORMATICA LTDA - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from erpbrasil.assinatura import misc

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.hooks import set_demo_product_fiscal_data
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files

from ..hooks import import_demo_nfe


def load_nfe_fixture_files(env):
    """Load the NF-e demo data as test fixtures.

    Odoo 19 installs no demo data by default, so the tests load the demo
    companies, the fiscal data and the NF-e demo documents they rely on.
    """
    if env.ref("l10n_br_nfe.demo_nfe_same_state", raise_if_not_found=False):
        return
    # the products of the core demo data first: the NF-e requires a product
    # code (cProd) and the expected XML files carry their codes and names;
    # without them load_fiscal_fixture_files would create empty products
    if not env.ref("product.product_product_10", raise_if_not_found=False):
        load_fixture_files(
            env,
            "product",
            file_names=[
                "data/product_attribute_demo.xml",
                "data/product_category_demo.xml",
                "data/product_demo.xml",
            ],
        )
    load_fiscal_fixture_files(env)
    set_demo_product_fiscal_data(env)
    _ensure_fake_certificates(env)
    # the expected XML files were generated with the core demo data: the name
    # of the demo user ends up in infAdFisco, and the timezone of the user
    # running the tests in the document dates
    user_demo = env.ref("base.user_demo")
    if user_demo.name != "Marc Demo":
        user_demo.write({"name": "Marc Demo", "tz": "Europe/Brussels"})
    if not env.user.tz:
        env.user.tz = "Europe/Brussels"
    # the companies first: the NF-e fields of the documents are only
    # computed for companies with the OCA processor
    load_fixture_files(
        env,
        "l10n_br_nfe",
        file_names=[
            "company_demo.xml",
            "fiscal_document_demo.xml",
        ],
    )
    # the supplier NF-e that the post_init_hook imports with demo data
    import_demo_nfe(env)


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
