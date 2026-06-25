# Copyright 2026 - TODAY Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


def load_account_nfe_fixture_files(env):
    """Load the demo data required by l10n_br_account_nfe tests as fixtures.

    This allows tests to run without depending on demo data being installed.
    """
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
