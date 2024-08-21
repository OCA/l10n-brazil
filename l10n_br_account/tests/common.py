# Copyright 2023 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import Form

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class AccountMoveBRCommon(AccountTestInvoicingCommon):
    """
    This is the base test suite for l10n_br_account with proper Brazilian
    Charts of Accounts and Brazilian data.
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # super().setUpClass() would duplicate some random IPI tax
        # we need to delete these duplicates to avoid errors:
        cls.tax_sale_b.unlink()
        cls.tax_purchase_b.unlink()

        cls.env.user.groups_id |= cls.env.ref("l10n_br_fiscal.group_manager")
        cls.product_a.write(
            {
                "default_code": "prod_a",
                "standard_price": 1000.0,
                "ncm_id": cls.env.ref("l10n_br_fiscal.ncm_94033000").id,
                "fiscal_genre_id": cls.env.ref("l10n_br_fiscal.product_genre_94").id,
                "fiscal_type": "00",
                "icms_origin": "5",
                "taxes_id": False,
                "tax_icms_or_issqn": "icms",
                "uoe_id": cls.env.ref("uom.product_uom_kgm").id,
            }
        )
        cls.fiscal_type_product_product_a = cls.env["ir.property"].create(
            {
                "name": "fiscal_type",
                "fields_id": cls.env["ir.model.fields"]
                .search(
                    [("model", "=", "product.template"), ("name", "=", "fiscal_type")]
                )
                .id,
                "value": "04",
                "type": "selection",
                "res_id": cls.product_a.id,
            }
        )
        cls.fiscal_origin_product_product_a = cls.env["ir.property"].create(
            {
                "name": "fiscal_origin",
                "fields_id": cls.env["ir.model.fields"]
                .search(
                    [("model", "=", "product.template"), ("name", "=", "icms_origin")]
                )
                .id,
                "value": "5",
                "type": "selection",
                "res_id": cls.product_a.id,
            }
        )

        cls.product_b.write(
            {
                "default_code": "prod_b",
                "lst_price": 1000.0,
                "ncm_id": cls.env.ref("l10n_br_fiscal.ncm_94013090").id,
                "fiscal_genre_id": cls.env.ref("l10n_br_fiscal.product_genre_94").id,
                "fiscal_type": "00",
                "icms_origin": "0",
                "taxes_id": False,
                "tax_icms_or_issqn": "icms",
                "uoe_id": cls.env.ref("uom.product_uom_kgm").id,
            }
        )
        cls.fiscal_type_product_product_b = cls.env["ir.property"].create(
            {
                "name": "fiscal_type",
                "fields_id": cls.env["ir.model.fields"]
                .search(
                    [("model", "=", "product.template"), ("name", "=", "fiscal_type")]
                )
                .id,
                "value": "00",
                "type": "selection",
                "res_id": cls.product_b.id,
            }
        )
        cls.fiscal_origin_product_product_b = cls.env["ir.property"].create(
            {
                "name": "fiscal_origin",
                "fields_id": cls.env["ir.model.fields"]
                .search(
                    [("model", "=", "product.template"), ("name", "=", "icms_origin")]
                )
                .id,
                "value": "0",
                "type": "selection",
                "res_id": cls.product_b.id,
            }
        )

        cls.partner_a.write(
            {
                "cnpj_cpf": "49.190.159/0001-05",
                "is_company": "1",
                "ind_ie_dest": "1",
                "tax_framework": "3",
                "legal_name": "partner A",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_rj").id,
                "district": "Centro",
                "zip": "01311-915",
                "fiscal_profile_id": cls.env.ref(
                    "l10n_br_fiscal.partner_fiscal_profile_snc"
                ).id,
            }
        )
        cls.partner_b.write(
            {
                "cnpj_cpf": "42.591.651/0001-43",
                "is_company": "0",
                "legal_name": "partner B",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_ba").id,
                "district": "Na PQP",
                "zip": "01311-942",
                "fiscal_profile_id": cls.env.ref(
                    "l10n_br_fiscal.partner_fiscal_profile_cnt"
                ).id,
            }
        )

        cls.partner_c = cls.partner_a.copy(
            {
                "name": "partner_c",
                "cnpj_cpf": "67.405.936/0001-73",
                "legal_name": "partner C",
                "fiscal_profile_id": cls.env.ref(
                    "l10n_br_fiscal.partner_fiscal_profile_ncn"
                ).id,
            }
        )

        cls.fo_sale_with_icms_reduction = cls.env[
            "l10n_br_fiscal.operation.line"
        ].create(
            {
                "name": "Venda com ICMS 12 e Redução de 26,57",
                "ind_ie_dest": "1",
                "cfop_internal_id": cls.env.ref("l10n_br_fiscal.cfop_5101").id,
                "cfop_external_id": cls.env.ref("l10n_br_fiscal.cfop_6101").id,
                "cfop_export_id": cls.env.ref("l10n_br_fiscal.cfop_7101").id,
                "state": "approved",
                "product_type": "04",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
            }
        )

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        """
        You might want to override it to force a single chart_template.
        The default behavior here is to load one for the SN and another for the LC.
        """
        cnpj_cpf = kwargs.get("cnpj_cpf", "")
        if company_name == "company_2_data":
            company_name = "empresa 2 Simples Nacional"
            chart_template = cls.env.ref(
                "l10n_br_coa_simple.l10n_br_coa_simple_chart_template"
            )
            cnpj_cpf = "30.360.463/0001-25"
        elif company_name == "company_1_data":
            company_name = "empresa 1 Lucro Presumido"
            chart_template = cls.env.ref(
                "l10n_br_coa_generic.l10n_br_coa_generic_template"
            )
            cnpj_cpf = "18.751.708/0001-40"

        kwargs.update(
            {
                "country_id": cls.env.ref("base.br").id,
                "currency_id": cls.env.ref("base.BRL").id,
                "is_industry": True,
                "cnpj_cpf": cnpj_cpf,
                "state_id": cls.env.ref("base.state_br_sp").id,
            }
        )
        return super().setup_company_data(company_name, chart_template, **kwargs)

    @classmethod
    def configure_normal_company_taxes(cls):
        # Tax configuration for normal company
        tax_def_model = cls.env["l10n_br_fiscal.tax.definition"]
        doc_serie_model = cls.env["l10n_br_fiscal.document.serie"]
        cls.pis_tax_definition_empresa_lc = tax_def_model.create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_pis").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_pis_0_65").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_pis_01").id,
                "state": "approved",
            }
        )

        cls.cofins_tax_definition_empresa_lc = tax_def_model.create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_cofins").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_cofins_3").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_cofins_01").id,
                "state": "approved",
            }
        )

        cls.icms_tax_definition_empresa_lc_icms_reduction = tax_def_model.create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icms").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_icms_12_red_26_57").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_icms_20").id,
                "state": "approved",
                "fiscal_operation_line_id": cls.fo_sale_with_icms_reduction.id,
            }
        )

        # Tax Definition for PIS and COFINS Withholding
        cls.pis_wh_tax_definition_empresa_lc = tax_def_model.create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_pis_wh").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_pis_wh_0_65").id,
                "state": "expired",
            }
        )

        cls.cofins_wh_tax_definition_empresa_lc = tax_def_model.create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_cofins_wh").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_cofins_wh_3").id,
                "state": "expired",
            }
        )

        cls.empresa_lc_document_55_serie_1 = doc_serie_model.create(
            {
                "code": "1",
                "name": "Série 1",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "active": True,
            }
        )

    @classmethod
    def init_invoice(
        cls,
        move_type,
        partner=None,
        invoice_date=None,
        post=False,
        products=None,
        amounts=None,
        taxes=None,
        currency=None,
        document_type=None,
        document_serie_id=None,
        fiscal_operation=None,
        fiscal_operation_lines=None,
        document_serie=None,
        document_number=None,
    ):
        """
        We could not override the super one because we need to inject extra BR fiscal fields.
        """
        products = [] if products is None else products
        amounts = [] if amounts is None else amounts
        move_form = Form(
            cls.env["account.move"].with_context(
                default_move_type=move_type,
                account_predictive_bills_disable_prediction=True,
            )
        )
        move_form.invoice_date = invoice_date or fields.Date.from_string("2019-01-01")
        #        move_form.date = move_form.invoice_date
        move_form.partner_id = partner or cls.partner_a
        move_form.currency_id = currency if currency else cls.company_data["currency"]

        # extra BR fiscal params:
        move_form.document_type_id = document_type
        if document_serie_id is not None:
            move_form.document_serie_id = document_serie_id
        move_form.fiscal_operation_id = fiscal_operation
        if document_number is not None:
            move_form.document_number = document_number
        if document_serie is not None:
            move_form.document_serie = document_serie

        for index, product in enumerate(products):
            with move_form.invoice_line_ids.new() as line_form:
                line_form.product_id = product

                # extra BR fiscal params:
                line_form.fiscal_operation_line_id = fiscal_operation_lines[index]

                if taxes:
                    line_form.tax_ids.clear()
                    line_form.tax_ids.add(taxes)

        for amount in amounts:
            with move_form.invoice_line_ids.new() as line_form:
                line_form.name = "test line"
                # We use account_predictive_bills_disable_prediction context key so that
                # this doesn't trigger prediction in case enterprise
                # (hence account_predictive_bills) is installed
                line_form.price_unit = amount
                if taxes:
                    line_form.tax_ids.clear()
                    for tax in taxes:
                        line_form.tax_ids.add(tax)

        rslt = move_form.save()

        if post:
            rslt.action_post()

        return rslt

    @classmethod
    def sort_lines(cls, lines):
        """
        Utility method to help debugging
        """
        return lines.sorted(
            lambda line: (
                line.exclude_from_invoice_tab,
                not bool(line.tax_line_id),
                line.name or "",
                line.balance,
            )
        )

    @classmethod
    def line_log(cls, lines, index):
        """
        Utility method to help debugging
        """
        lines = cls.sort_lines(lines.sorted())
        log = "LINE %s %s %s %s %s" % (
            index,
            lines[index].name,
            lines[index].debit,
            lines[index].credit,
            lines[index].account_id.name,
        )
        return log
