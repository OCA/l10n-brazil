# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import sys

from odoo import SUPERUSER_ID, api, registry as odoo_registry
from odoo.modules import loading
from odoo.tools.sql import column_exists, create_column

_logger = logging.getLogger(__name__)


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
    if not column_exists(cr, "account_invoice", "fiscal_document_id"):
        create_column(cr, "account_invoice", "fiscal_document_id", "INTEGER")

    # Create fiscal_document_line_id fields
    if not column_exists(cr, "account_invoice_line", "fiscal_document_line_id"):
        create_column(cr, "account_invoice_line", "fiscal_document_line_id", "INTEGER")

    companies = env["res.company"].search([])
    for company in companies:
        cr.execute(
            """
            UPDATE
                account_invoice
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
                account_invoice_line
            SET
                fiscal_document_line_id=%s
            WHERE
                company_id=%s
            AND
                fiscal_document_line_id IS NULL;""",
            (company.fiscal_dummy_id.line_ids[0].id, company.id),
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
