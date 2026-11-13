# Copyright 2026 - TODAY Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_account.tests.common import load_demo_company_chart
from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


def load_account_nfe_fixture_files(env):
    """Load the demo data required by l10n_br_account_nfe tests as fixtures.

    This allows tests to run without depending on demo data being installed.
    """
    # Load the fixtures as the demo data is loaded at install time: as
    # superuser, with the main company active. The fiscal product demo data
    # sets company-dependent fields (fiscal_type, icms_origin...) for the
    # active company, and the companies created by the test framework have no
    # ICMS regulation; the test users may not have access to the main company.
    main_company = env.ref("base.main_company")
    env = env(su=True, context=dict(env.context, allowed_company_ids=main_company.ids))
    # The products of the core demo data first: the tests rely on their prices
    # (e.g. product_product_5), and without them load_fiscal_fixture_files
    # would create empty products
    if not env.ref("product.product_product_5", raise_if_not_found=False):
        load_fixture_files(
            env,
            "product",
            file_names=[
                "data/product_attribute_demo.xml",
                "data/product_category_demo.xml",
                "data/product_demo.xml",
            ],
        )

    # Base + fiscal demo data (partners, companies, products, operations...)
    load_fiscal_fixture_files(env)

    # l10n_br_nfe fiscal document demo data (demo_nfce_same_state etc.)
    load_fixture_files(
        env,
        "l10n_br_nfe",
        file_names=[
            "company_demo.xml",
            "fiscal_document_demo.xml",
        ],
    )

    # l10n_br_account_nfe own demo data (payment terms, journals, payment modes)
    load_fixture_files(
        env,
        "l10n_br_account_nfe",
        file_names=[
            "account_invoice_sn_demo.xml",
        ],
    )

    # The demo companies have no chart of accounts without demo data (it is
    # installed by l10n_br_coa_generic): the NF-e import needs its journals.
    load_demo_company_chart(env)
