# Copyright (C) 2019 - Raphaël Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists, create_column


def pre_init_hook(cr):
    """
    account.invoice and account.invoice.line inherits from
    l10n_br_account.fiscal_document and l10n_br_account.fiscal_document.line
    respectively.
    But the problem is that you may have existing invoice and lines (like demo
    data or because you were using Odoo before installing this module or because
    you use your Odoo instance for other countries than Brazil) so we should
    make the Odoo ORM happy for these records and we do that with dummy records
    that we use to fill these new foreign keys.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    if not column_exists(cr, "account_invoice", "fiscal_document_id"):
        create_column(cr, "account_invoice", "fiscal_document_id", "INTEGER")
    fiscal_doc_id = env.ref("l10n_br_fiscal.fiscal_document_dummy").id
    cr.execute(
        """update account_invoice set fiscal_document_id=%s
               where fiscal_document_id IS NULL;""",
        (fiscal_doc_id,),
    )
    fiscal_doc_line_id = env.ref("l10n_br_fiscal.fiscal_document_line_dummy").id
    if not column_exists(cr, "account_invoice_line", "fiscal_document_line_id"):
        create_column(cr, "account_invoice_line", "fiscal_document_line_id", "INTEGER")
    cr.execute(
        """update account_invoice_line set fiscal_document_line_id=%s
               where fiscal_document_line_id IS NULL;""",
        (fiscal_doc_line_id,),
    )


def set_accounts(env, l10n_br_coa_chart):
    module = 'l10n_br_account'
    company_id = env.user.company_id.id
    mapping = {
        'line_receita_icms': 'icms_sale',
        'line_receita_icms_st': 'icms_st_sale',
        'line_receita_ipi': 'ipi_sale',
        'line_receita_pis': 'pis_sale',
        'line_receita_cofins': 'cofins_sale',
        'line_receita_venda': 'sale_revenue',
        'line_receita_revenda': 'resale_revenue',
        'line_receita_venda_st': 'sale_st_revenue',
        'line_receita_revenda_st': 'resale_st_revenue',
        'line_devolucao_venda': 'sale_return',
        'line_devolucao_compra': 'purchase_return',
        'line_receita_simples_nacional': 'simple_national',
    }
    for line_ref, field in mapping.items():
        line = env.ref(module + '.' + line_ref)
        acc = l10n_br_coa_chart[field + '_credit_id']
        acc_ref = acc.get_external_id().get(acc.id)
        if acc_ref:
            ref_module, ref_name = acc_ref.split('.')
            line.account_credit_id = env.ref('%s.%s_%s' % (
                ref_module, company_id, ref_name))
        acc = l10n_br_coa_chart[field + '_debit_id']
        acc_ref = acc.get_external_id().get(acc.id)
        if acc_ref:
            ref_module, ref_name = acc_ref.split('.')
            line.account_debit_id = env.ref('%s.%s_%s' % (
                ref_module, company_id, ref_name))


def load_fiscal_taxes(env, l10n_br_coa_chart):
    companies = env["res.company"].search(
        [("chart_template_id", "=", l10n_br_coa_chart.id)]
    )

    original_company = env.user.company_id

    for company in companies:
        taxes = env["account.tax"].search([("company_id", "=", company.id)])

        env.user.company_id = company
        set_accounts(env, l10n_br_coa_chart)

        for tax in taxes:
            if tax.get_external_id():
                tax_ref = tax.get_external_id().get(tax.id)
                ref_module, ref_name = tax_ref.split(".")
                ref_name = ref_name.replace(str(company.id) + "_", "")
                template_source_ref = ".".join(["l10n_br_coa", ref_name])
                template_source = env.ref(template_source_ref)
                tax_source_ref = ".".join([ref_module, ref_name])
                tax_template = env.ref(tax_source_ref)
                tax.fiscal_tax_ids = tax_template.fiscal_tax_ids = \
                    template_source.fiscal_tax_ids

    env.user.company_id = original_company


def post_init_hook(cr, registry):
    """Relate fiscal taxes to account taxes."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    l10n_br_coa_charts = env["account.chart.template"].search([]).filtered(
        lambda chart: chart.get_external_id().get(
            chart.id).split('.')[0].startswith("l10n_br_coa_")
        if chart.get_external_id().get(chart.id) else False
    )
    for l10n_br_coa_chart in l10n_br_coa_charts:
        load_fiscal_taxes(env, l10n_br_coa_chart)
