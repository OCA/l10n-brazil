# Copyright (C) 2024 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files


def load_purchase_fixture_files(env):
    """Load purchase demo data as test fixtures.

    This allows tests to run without depending on demo data being installed.
    The fixture files are loaded dynamically in setUpClass.
    """
    load_fixture_files(
        env,
        "l10n_br_purchase",
        file_names=[
            "company.xml",
            "product.xml",
            "l10n_br_purchase.xml",
        ],
    )
