# Copyright (C) 2024 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo.addons.l10n_br_account.tests.common import load_demo_company_chart
from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files

_logger = logging.getLogger(__name__)


def load_sale_fixture_files(env):
    """Load sale demo data as test fixtures.

    This allows tests to run without depending on demo data being installed.
    The fixture files are loaded dynamically in setUpClass.
    """
    # base/fiscal fixtures: demo companies, partners, products, fiscal taxes
    load_fiscal_fixture_files(env)

    # demo users of the Brazilian demo companies (user_demo_simples,
    # user_demo_presumido, user_demo_real) used as salespersons by the sale
    # demo orders. They are not part of load_fiscal_fixture_files.
    if not env.ref("l10n_br_base.user_demo_simples", raise_if_not_found=False):
        load_fixture_files(env, "l10n_br_base", file_names=["res_users_demo.xml"])

    # demo data of the sale/sales_team modules referenced by the l10n_br_sale
    # demo data: the sales team and the down payment product / international
    # demo order. The sale data/ files cannot be loaded as such: they contain
    # updates of product/sale demo records of other modules, so the few
    # records the sale demo data needs are fabricated here instead (same
    # approach as load_fiscal_fixture_files).
    if not env.ref("sales_team.crm_team_1", raise_if_not_found=False):
        load_fixture_files(env, "sales_team", file_names=["data/crm_team_demo.xml"])
    _ensure_advance_product_fixture(env)
    _ensure_international_order_fixture(env)

    # The demo companies created by the fixtures have no chart of accounts and
    # the fiscal configuration of the demo products is company dependent, so
    # load both for the companies used by the sale demo orders. This MUST
    # happen before the l10n_br_sale demo data is loaded: the fiscal
    # operation/CFOP of a sale order line is computed at creation time from
    # the company and partner location, and a company that is not Brazilian
    # yet makes every line resolve to an export CFOP.
    load_demo_company_chart(env, "l10n_br_base.empresa_simples_nacional")
    load_demo_company_chart(env, "l10n_br_base.empresa_lucro_presumido")
    _ensure_brazilian_company(env, "l10n_br_base.empresa_simples_nacional")
    _ensure_brazilian_company(env, "l10n_br_base.empresa_lucro_presumido")
    _setup_main_company(env)

    # NOTE: res.company.country_id/state_id are empty in this 19.0 port (core
    # turned them into a computed address field, and the module MRO ends up
    # with the core _compute_address while l10n_br_base declares the field as
    # its own stored field with a base.br default). Consequence for tests: any
    # sale order line created here resolves to an EXPORT CFOP (7101) instead of
    # the internal/external one, and the Brazilian-only fields of the sale
    # order form (invisible="company_country_id != base.br") stay invisible.
    # This is reproducible WITH demo data as well, so it has to be fixed in
    # l10n_br_base (company address) rather than worked around here.
    load_fixture_files(
        env,
        "l10n_br_sale",
        file_names=[
            "company.xml",
            "product.xml",
            "l10n_br_sale.xml",
        ],
    )


def _register_xmlid(env, module, name, model, res_id):
    env["ir.model.data"].create(
        {
            "name": name,
            "module": module,
            "res_id": res_id,
            "model": model,
            "noupdate": True,
        }
    )


def _ensure_advance_product_fixture(env):
    """Provide sale.advance_product_0 without the sale demo data.

    The l10n_br_sale demo data updates that down payment product, and the
    sale data/product_demo.xml file cannot be loaded as such (it also updates
    product demo records that do not exist without demo data).
    """
    if env.ref("sale.advance_product_0", raise_if_not_found=False):
        return
    product = env["product.product"].create(
        {
            "name": "Deposit",
            "type": "service",
            "list_price": 150.0,
            "standard_price": 100.0,
            "invoice_policy": "order",
            "uom_id": env.ref("uom.product_uom_unit").id,
            "company_id": False,
        }
    )
    _register_xmlid(env, "sale", "advance_product_0", "product.product", product.id)


def _ensure_international_order_fixture(env):
    """Provide sale.sale_order_2 without the sale demo data.

    It is the international (non Brazilian) sale order used by
    test_compatible_with_international_case: a foreign customer and no
    fiscal operation. The core demo data file cannot be loaded as such
    because it references demo partners, teams and utm records.
    """
    if env.ref("sale.sale_order_2", raise_if_not_found=False):
        return
    partner = env["res.partner"].create(
        {
            "name": "Fixture International Customer",
            "country_id": env.ref("base.us").id,
        }
    )
    order = env["sale.order"].create(
        {
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": partner.id,
            "user_id": env.uid,
            "company_id": env.ref("base.main_company").id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": env.ref("product.product_product_1").id,
                        "product_uom_qty": 24.0,
                        "price_unit": 75.0,
                    },
                )
            ],
        }
    )
    _register_xmlid(env, "sale", "sale_order_2", "sale.order", order.id)


def _ensure_brazilian_company(env, company_xmlid):
    """Give a Brazilian demo company the address it needs.

    ``l10n_br_base/demo/res_company_demo.xml`` only sets the ``partner_id`` of
    the demo companies, and since Odoo 19 ``res.company.country_id``/
    ``state_id`` are computed address fields that read empty (the address is
    stored on the company partner). A company without country makes every
    fiscal operation line resolve to an export CFOP and hides the Brazilian
    fields of the sale order form, so set the address on the partner.
    """
    company = env.ref(company_xmlid)
    partner = company.partner_id
    if partner.country_id != env.ref("base.br"):
        # force the Brazilian address: in a database installed without demo
        # data the demo company partner can end up with the country of the
        # main company (US), which makes the fiscal engine see a foreign
        # company (export CFOP) and hides the Brazilian fields of the forms.
        partner.write(
            {
                "country_id": env.ref("base.br").id,
                "state_id": env.ref("base.state_br_sp").id,
            }
        )
    return company


def _setup_main_company(env):
    """Make the main company usable for Brazilian sale orders.

    Several sale tests use the demo sale orders of the main company. With demo
    data, the l10n_br_account post_init_hook configures it as a Brazilian
    company; without demo data it is left untouched (base.main_company is not
    a Brazilian company at all). Mirror the part the sale tests need: a
    Brazilian address, the chart of accounts with the fiscal taxes and the
    sale journal of the fiscal operation, so the orders can be invoiced.
    """
    main_company = env.ref("base.main_company")
    # the company address is stored on the company partner (see
    # _ensure_brazilian_company)
    main_partner = main_company.partner_id
    if main_partner.country_id.code != "BR":
        main_partner.write(
            {
                "country_id": env.ref("base.br").id,
                "state_id": env.ref("base.state_br_sp").id,
            }
        )
    if not main_company.chart_template:
        env["account.chart.template"].try_loading("generic_coa", main_company)
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

    sale_journal = env["account.journal"].search(
        [("company_id", "=", main_company.id), ("type", "=", "sale")],
        limit=1,
    )
    fiscal_operation = env.ref("l10n_br_fiscal.fo_venda")
    if sale_journal and not fiscal_operation.with_company(main_company).journal_id:
        fiscal_operation.with_company(main_company).journal_id = sale_journal
