# Copyright (C) 2024 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo.addons.l10n_br_account.tests.common import load_demo_company_chart
from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files

_logger = logging.getLogger(__name__)


def load_purchase_fixture_files(env):
    """Load purchase demo data as test fixtures.

    This allows tests to run without depending on demo data being installed.
    The fixture files are loaded dynamically in setUpClass.
    """
    # base/fiscal fixtures: demo companies, partners, products, fiscal taxes
    load_fiscal_fixture_files(env)

    # demo purchase orders of the purchase module (international case).
    # They live in data/ (not demo/) since Odoo 19.
    if not env.ref("purchase.purchase_order_1", raise_if_not_found=False):
        load_fixture_files(env, "purchase", file_names=["data/purchase_demo.xml"])

    _ensure_payment_term_fixture(env)
    _setup_main_company(env)

    load_fixture_files(
        env,
        "l10n_br_purchase",
        file_names=[
            "company.xml",
            "product.xml",
            "l10n_br_purchase.xml",
        ],
    )

    # the demo companies created by the fixtures have no chart of accounts and
    # the fiscal configuration of the demo products is company dependent, so
    # load both for the purchase demo company.
    return load_demo_company_chart(env)


def _ensure_payment_term_fixture(env):
    """Provide account.account_payment_term_advance without account demo data.

    The purchase demo data references that payment term, which only exists when
    the account demo data is installed. Create a stand-in record carrying the
    same xmlid, the same way load_fiscal_fixture_files does for the base and
    product demo records.
    """
    if env.ref("account.account_payment_term_advance", raise_if_not_found=False):
        return
    term = env["account.payment.term"].create(
        {"name": "30% Advance End of Following Month"}
    )
    env["ir.model.data"].create(
        {
            "name": "account_payment_term_advance",
            "module": "account",
            "res_id": term.id,
            "model": "account.payment.term",
            "noupdate": True,
        }
    )


def _setup_main_company(env):
    """Make the main company usable for Brazilian purchase invoices.

    Several purchase tests use the demo purchase orders of the main company.
    With demo data, the l10n_br_account/l10n_br_purchase post_init_hooks
    configure it as a Brazilian company for tests; without demo data they skip
    it (base.main_company has no fiscal configuration at all). Mirror the part
    the purchase tests need: a Brazilian address and the purchase journal of
    the fiscal operation, so invoices can be created the same way.
    """
    main_company = env.ref("base.main_company")
    if main_company.country_id.code != "BR":
        main_company.write(
            {
                "country_id": env.ref("base.br").id,
                "state_id": env.ref("base.state_br_sp").id,
            }
        )
    if not main_company.chart_template:
        # _load() is what try_loading() wraps: it does not warn about a not
        # fully loaded registry, which is the case while the tests are running.
        env["account.chart.template"]._load(
            "generic_coa", main_company, install_demo=False
        )
    chart_mapping = env["account.chart.template"]._get_chart_template_mapping()
    if chart_mapping.get(main_company.chart_template):
        # load_fiscal_taxes needs a known chart template: it creates the
        # Brazilian tax accounts of the chart.
        env["account.chart.template"].load_fiscal_taxes([main_company])
    else:
        _logger.warning(
            "No chart template mapped for %s (%s): fiscal taxes not loaded",
            main_company.name,
            main_company.chart_template,
        )

    purchase_journal = env["account.journal"].search(
        [("company_id", "=", main_company.id), ("type", "=", "purchase")],
        limit=1,
    )
    fiscal_operation = env.ref("l10n_br_fiscal.fo_compras")
    if purchase_journal and not fiscal_operation.with_company(main_company).journal_id:
        fiscal_operation.with_company(main_company).journal_id = purchase_journal
