# Copyright (C) 2026-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form


def create_with_form_br_stock_picking(env, values, line_values=False):
    with Form(env["stock.picking"].with_company(values.get("company_id"))) as picking:
        picking.partner_id = values.get("partner_id")
        picking.picking_type_id = values.get("picking_type_id")
        picking.invoice_state = "2binvoiced"
        picking.fiscal_operation_id = values.get("fiscal_operation_id")
        for value in line_values:
            with picking.move_ids_without_package.new() as line:
                line.product_id = value.get("product_id")
                line.product_uom_qty = value.get("product_uom_qty")

    return picking.save()


def create_with_form_br_account_journal(env, values):
    with Form(env["account.journal"].with_company(values.get("company_id"))) as journal:
        journal.name = values.get("name")
        journal.code = values.get("code")
        journal.type = values.get("type")
        journal.default_account_id = values.get("default_account_id")
    return journal.save()


def create_and_configure_br_company(env, company_values, fiscal_ops):
    company = env["res.company"].create(company_values)
    env.user.company_ids |= company
    create_br_minimal_chart(env, company)
    create_br_journal_and_set_fiscal_ops(env, company, fiscal_ops)
    return company


def create_br_minimal_chart(env, company):
    # Load chart template company if not already loaded
    has_receivable = (
        env["account.account"]
        .with_company(company)
        .search_count([("account_type", "=", "asset_receivable")])
    )

    if not has_receivable:
        # Create minimal chart accounts for company
        # to avoid depending on l10n_br chart template
        account_vals = [
            {
                "name": "Receivable",
                "code": "1.1.1.01",
                "account_type": "asset_receivable",
                "company_ids": [(4, company.id)],
                "reconcile": True,
            },
            {
                "name": "Payable",
                "code": "2.1.1.01",
                "account_type": "liability_payable",
                "company_ids": [(4, company.id)],
                "reconcile": True,
            },
            {
                "name": "Income",
                "code": "3.1.1.01",
                "account_type": "income",
                "company_ids": [(4, company.id)],
            },
            {
                "name": "Expense",
                "code": "4.1.1.01",
                "account_type": "expense",
                "company_ids": [(4, company.id)],
            },
            {
                "name": "EXpense Direct Cost",
                "code": "4.1.1.10",
                "account_type": "expense_direct_cost",
                "company_ids": [(4, company.id)],
            },
        ]
        accounts = env["account.account"].create(account_vals)
        receivable_account = accounts.filtered(
            lambda a: a.account_type == "asset_receivable"
        )
        income_account = accounts.filtered(lambda a: a.account_type == "income")
        expense_account = accounts.filtered(lambda a: a.account_type == "expense")
        # Set default company accounts
        company.account_journal_suspense_account_id = receivable_account.id
        # Set product category accounts for this company
        product_category = env.ref("product.product_category_all")
        product_category.with_company(
            company
        ).property_account_income_categ_id = income_account
        product_category.with_company(
            company
        ).property_account_expense_categ_id = expense_account
        # Load fiscal taxes for the company
        if not company.chart_template:
            chart_template = env["account.chart.template"]
            chart_template.try_loading("generic_coa", company, install_demo=False)
        env["account.chart.template"].load_fiscal_taxes(companies=[company])


def create_br_journal_and_set_fiscal_ops(env, company, fiscal_ops, journal_type="sale"):
    """Create a Journal and set it on the given Brazilian Fiscal Operations.

    :param journal_type: "sale" (default, used by the Outgoing Fiscal
        Operations) or "purchase" (needed when the document created from the
        Picking is a purchase one, ex.: the return of an Incoming Picking, which
        is invoiced as in_refund).
    """
    doc_type_55 = env["l10n_br_fiscal.document.type"].search([("code", "=", "55")])
    company.document_type_id = doc_type_55
    if not env["l10n_br_fiscal.document.serie"].search(
        [("company_id", "=", company.id), ("document_type_id", "=", doc_type_55.id)],
        limit=1,
    ):
        env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "Série 1",
                "document_type_id": doc_type_55.id,
                "company_id": company.id,
                "active": True,
            }
        )

    account_revenue = env["account.account"].search(
        [
            ("account_type", "=", "expense_direct_cost"),
            ("company_ids", "in", (company.id)),
        ],
        limit=1,
    )
    data_journal_base = {
        "type": journal_type,
        "default_account_id": account_revenue,
        "company_id": company,
    }
    for fiscal_op in fiscal_ops:
        code = fiscal_op.name[:3]
        if journal_type != "sale":
            # Evita o conflito de código com o Diário da mesma Operação Fiscal
            code = (journal_type[:1] + fiscal_op.name)[:3]
        data_journal = data_journal_base | {
            "name": "Diário" + fiscal_op.name,
            "code": code.upper(),
        }
        journal = create_with_form_br_account_journal(env, data_journal)
        fiscal_op.with_company(company).journal_id = journal
