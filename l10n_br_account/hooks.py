# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import random
import sys
import time
from datetime import datetime

from faker import Faker

from odoo import SUPERUSER_ID, api, registry as odoo_registry
from odoo.modules import loading
from odoo.tools.sql import column_exists, create_column

_logger = logging.getLogger(__name__)
fake = Faker()


def pre_init_hook(cr):
    """
    account.move and account.move.line inherits from
    l10n_br_account.fiscal_document and l10n_br_account.fiscal_document.line
    respectively.
    But the problem is that you may have existing invoice and lines (like demo
    data or because you were using Odoo before installing this module or because
    you use your Odoo instance for other countries than Brazil) so we should
    make the Odoo ORM happy for these records and we do that with dummy records
    that we use to fill these new foreign keys.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    cr.execute("select demo from ir_module_module where name='l10n_br_account';")
    is_demo = cr.fetchone()[0]
    if is_demo:
        # load convenient COAs that are used in demos and tests
        # without a hard dependency (you don't need all COAs for production)
        coa_modules = env["ir.module.module"].search(
            [
                ("name", "in", ("l10n_br_coa_generic", "l10n_br_coa_simple")),
                ("state", "=", "uninstalled"),
            ]
        )

        if coa_modules:
            registry = odoo_registry(cr.dbname)

            # this xmlids hack is required to avoid deletion records
            # just installed before this hook and before loaded_xmlids would
            # be reset by load_modules.
            loaded_xmlids = registry.loaded_xmlids.copy()

            # without this, these modules would be installed twice
            to_install = env["ir.module.module"].search([("state", "=", "to install")])
            to_upgrade = env["ir.module.module"].search([("state", "=", "to upgrade")])
            (to_install + to_upgrade).write({"state": "uninstalled"})

            # strangely setting coa_modules as 'to install' would fail
            coa_modules.write({"state": "to upgrade"})
            # we need to commit so load_modules can see it.
            # load_modules would commit soon after anyway.
            cr.commit()  # pylint: disable=E8102
            _logger.info("installing charts of accounts for demo context...")
            loading.load_modules(registry._db, force_demo=True)
            # this 2nd commit is required to be able to call the post_init_hook
            cr.commit()  # pylint: disable=E8102
            for mod in coa_modules:
                py_module = sys.modules["odoo.addons.%s" % (mod.name,)]
                py_module.post_init_hook(cr, registry)

            to_install.write({"state": "to install"})
            to_upgrade.write({"state": "to upgrade"})
            registry.loaded_xmlids = loaded_xmlids.union(registry.loaded_xmlids)

    # Create fiscal_document_id fields
    if not column_exists(cr, "account_move", "fiscal_document_id"):
        create_column(cr, "account_move", "fiscal_document_id", "INTEGER")

    # Create fiscal_document_line_id fields
    if not column_exists(cr, "account_move_line", "fiscal_document_line_id"):
        create_column(cr, "account_move_line", "fiscal_document_line_id", "INTEGER")

    companies = env["res.company"].search([])
    for company in companies:
        cr.execute(
            """
            UPDATE
                account_move
            SET fiscal_document_id=%s
            WHERE
                company_id=%s
            AND
                fiscal_document_id IS NULL;""",
            (company.fiscal_dummy_id.id, company.id),
        )
        cr.execute(
            """
            UPDATE
                account_move_line
            SET
                fiscal_document_line_id=%s
            WHERE
                company_id=%s
            AND
                fiscal_document_line_id IS NULL;""",
            (company.fiscal_dummy_id.fiscal_line_ids[0].id, company.id),
        )


def load_fiscal_taxes(env, l10n_br_coa_chart):
    companies = env["res.company"].search(
        [("chart_template_id", "=", l10n_br_coa_chart.id)]
    )

    for company in companies:
        taxes = env["account.tax"].search([("company_id", "=", company.id)])

        for tax in taxes:
            if tax.get_external_id():
                tax_ref = tax.get_external_id().get(tax.id)
                ref_module, ref_name = tax_ref.split(".")
                ref_name = ref_name.replace(str(company.id) + "_", "")
                template_source_ref = ".".join(["l10n_br_coa", ref_name])
                template_source = env.ref(template_source_ref)
                tax_source_ref = ".".join([ref_module, ref_name])
                tax_template = env.ref(tax_source_ref)
                tax.fiscal_tax_ids = (
                    tax_template.fiscal_tax_ids
                ) = template_source.fiscal_tax_ids


def post_init_hook(cr, registry):
    """Relate fiscal taxes to account taxes."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    l10n_br_coa_charts = env["account.chart.template"].search(
        [("parent_id", "=", env.ref("l10n_br_coa.l10n_br_coa_template").id)]
    )

    for l10n_br_coa_chart in l10n_br_coa_charts:
        load_fiscal_taxes(env, l10n_br_coa_chart)

    # populating a database with dummy data
    num_records = 1000
    _logger.info("Populating a database with %s dummy records", num_records)
    partner_ids = env["res.partner"].search([]).ids
    product_ids = env["product.product"].search([]).ids
    start_date = datetime.strptime("2020-01-01", "%Y-%m-%d").date()
    end_date = datetime.strptime("2023-12-31", "%Y-%m-%d").date()
    for i in range(num_records):
        start_time = time.perf_counter()
        create_account_move_fake(env, partner_ids, product_ids, start_date, end_date)
        elapsed_time = time.perf_counter() - start_time
        _logger.info(
            f"Created the invoice {i} of {num_records}. time: {elapsed_time:.6f} seconds"
        )
        env.cr.commit()


def create_account_move_fake(env, partner_ids, product_ids, start_date, end_date):
    env["account.move"].create(
        {
            "move_type": "out_invoice",
            "partner_id": random.choice(partner_ids),
            "invoice_date": fake.date_between(start_date=start_date, end_date=end_date),
            "invoice_line_ids": create_account_move_lines_fake_data(10, product_ids),
        }
    )


def create_account_move_lines_fake_data(num_records, product_ids):
    data = []
    for _ in range(num_records):
        data.append(
            (
                0,
                0,
                {
                    "product_id": random.choice(product_ids),
                    "quantity": random.randint(1, 100),
                    "price_unit": round(fake.random.uniform(1, 100), 2),
                },
            )
        )
    return data
