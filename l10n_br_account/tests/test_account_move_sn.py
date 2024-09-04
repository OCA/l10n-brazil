# Copyright 2023 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class AccountMoveSimpleNacional(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.icms_tax_definition_empresa_simples_nacional = cls.env[
            "l10n_br_fiscal.tax.definition"
        ].create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icmssn").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_icmssn_101").id,
                "state": "approved",
            }
        )

        cls.empresa_sn_document_55_serie_1 = cls.env[
            "l10n_br_fiscal.document.serie"
        ].create(
            {
                "code": "1",
                "name": "Série 1",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "active": True,
            }
        )
        cls.move_out_revenda = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_sn_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_revenda")],
        )

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        if company_name == "company_1_data":
            company_name = "empresa 1 Simples Nacional"
        else:
            company_name = "empresa 2 Simples Nacional"
        chart_template = cls.env.ref(
            "l10n_br_coa_simple.l10n_br_coa_simple_chart_template"
        )
        res = super().setup_company_data(
            company_name,
            chart_template,
            tax_framework="1",
            is_industry=True,
            coefficient_r=False,
            ripi=True,
            piscofins_id=cls.env.ref(
                "l10n_br_fiscal.tax_pis_cofins_simples_nacional"
            ).id,
            tax_ipi_id=cls.env.ref("l10n_br_fiscal.tax_ipi_outros").id,
            tax_icms_id=cls.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito").id,
            cnae_main_id=cls.env.ref("l10n_br_fiscal.cnae_3101200").id,
            document_type_id=cls.env.ref("l10n_br_fiscal.document_55").id,
            annual_revenue=815000.0,
            **kwargs,
        )
        chart_template.load_fiscal_taxes()
        return res

    def test_company_sn_config(self):
        self.assertEqual(
            self.company_data["company"].simplified_tax_id.name, "Anexo 2 - Indústria"
        )
        self.assertEqual(self.company_data["company"].simplified_tax_percent, 8.44)
        self.assertEqual(
            self.company_data["company"].simplified_tax_range_id.name, "Faixa 4"
        )

    def test_revenda_fiscal_lines(self):
        self.assertEqual(
            self.move_out_revenda.invoice_line_ids[0].cfop_id.name,
            "Venda de mercadoria adquirida ou recebida de terceiros",
        )
        self.assertEqual(
            self.move_out_revenda.invoice_line_ids[0].icmssn_tax_id,
            self.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito"),
        )
        self.assertEqual(
            self.move_out_revenda.invoice_line_ids[0].icms_cst_id,
            self.env.ref("l10n_br_fiscal.cst_icmssn_101"),
        )
        self.assertEqual(self.move_out_revenda.invoice_line_ids[0].icmssn_percent, 2.70)

    def test_revenda(self):
        product_line_vals_1 = {
            "name": self.product_a.display_name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1000.0,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -973.0,
            "debit": 0.0,
            "credit": 973.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS - Simples Nacional",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": False,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS SN Saida")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -27.0,
            "debit": 0.0,
            "credit": 27.0,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "",
            "product_id": False,
            "account_id": self.company_data["default_account_receivable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": False,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1000.0,
            "debit": 1000.0,
            "credit": 0.0,
            "date_maturity": fields.Date.from_string("2019-01-01"),
        }

        move_vals = {
            "partner_id": self.partner_a.id,
            "currency_id": self.company_data["currency"].id,
            "journal_id": self.company_data["default_journal_sale"].id,
            "date": fields.Date.from_string("2019-01-01"),
            "fiscal_position_id": False,
            "payment_reference": "",
            "invoice_payment_term_id": self.pay_terms_a.id,
            "amount_untaxed": 1000.0,
            "amount_tax": 0.0,
            "amount_total": 1000.0,
        }

        self.assertInvoiceValues(
            self.move_out_revenda,
            [
                product_line_vals_1,
                tax_line_vals_icms,
                term_line_vals_1,
            ],
            move_vals,
        )
