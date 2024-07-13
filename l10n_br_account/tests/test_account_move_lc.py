# Copyright 2023 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class AccountMoveLucroPresumido(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.configure_normal_company_taxes()

        cls.move_out_venda = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )

        cls.move_out_venda_with_icms_reduction = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.fo_sale_with_icms_reduction],
        )

        cls.move_out_simples_remessa = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_simples_remessa"),
            fiscal_operation_lines=[
                cls.env.ref("l10n_br_fiscal.fo_simples_remessa_simples_remessa")
            ],
        )

        cls.env.ref("l10n_br_fiscal.fo_compras").deductible_taxes = True
        cls.move_in_compra_para_revenda = cls.init_invoice(
            "in_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                cls.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="42",
        )

        # Account Moves With Tax Withholding
        cls.pis_tax_definition_empresa_lc.state = "expired"
        cls.cofins_tax_definition_empresa_lc.state = "expired"
        cls.pis_wh_tax_definition_empresa_lc.action_approve()
        cls.cofins_wh_tax_definition_empresa_lc.action_approve()

        cls.move_out_venda_tax_withholding = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )

        cls.move_out_simples_remessa_tax_withholding = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_simples_remessa"),
            fiscal_operation_lines=[
                cls.env.ref("l10n_br_fiscal.fo_simples_remessa_simples_remessa")
            ],
        )

        cls.env.ref("l10n_br_fiscal.fo_compras").deductible_taxes = True
        cls.move_in_compra_para_revenda_tax_withholding = cls.init_invoice(
            "in_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                cls.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="44",
        )

        # Set default values for the tax definitions
        cls.pis_tax_definition_empresa_lc.action_approve()
        cls.cofins_tax_definition_empresa_lc.action_approve()
        cls.pis_wh_tax_definition_empresa_lc.state = "expired"
        cls.cofins_wh_tax_definition_empresa_lc.state = "expired"

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        if company_name == "company_1_data":
            company_name = "empresa 1 Lucro Presumido"
        else:
            company_name = "empresa 2 Lucro Presumido"
        chart_template = cls.env.ref("l10n_br_coa_generic.l10n_br_coa_generic_template")
        res = super().setup_company_data(
            company_name,
            chart_template,
            tax_framework="3",
            is_industry=True,
            industry_type="00",
            profit_calculation="presumed",
            ripi=True,
            piscofins_id=cls.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo").id,
            icms_regulation_id=cls.env.ref("l10n_br_fiscal.tax_icms_regulation").id,
            cnae_main_id=cls.env.ref("l10n_br_fiscal.cnae_3101200").id,
            document_type_id=cls.env.ref("l10n_br_fiscal.document_55").id,
            **kwargs
        )
        res["company"].partner_id.state_id = cls.env.ref("base.state_br_sp").id
        chart_template.load_fiscal_taxes()
        return res

    def test_venda_fiscal_lines(self):
        self.assertEqual(
            self.move_out_venda.invoice_line_ids[0].cfop_id.name,
            "Venda de produção do estabelecimento",
        )

    def test_venda(self):
        product_line_vals_1 = {
            "name": self.product_a.name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1050.0,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -843.5,
            "debit": 0.0,
            "credit": 843.5,
            "date_maturity": False,
        }

        tax_line_vals_cofins = {
            "name": "COFINS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 30.0,
            "price_subtotal": 30.0,
            "price_total": 30.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS Saida")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -30.0,
            "debit": 0.0,
            "credit": 30.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 120.0,
            "price_subtotal": 120.0,
            "price_total": 120.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
        }

        tax_line_vals_ipi = {
            "name": "IPI Saída",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "IPI a Recolher"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                order="id ASC",
                limit=1,
            )
            .id,  # TODO find our why this complex domain is required for IPI
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 50.0,
            "price_subtotal": 50.0,
            "price_total": 50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Saída")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
        }

        tax_line_vals_pis = {
            "name": "PIS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 6.5,
            "price_subtotal": 6.5,
            "price_total": 6.5,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "",
            "product_id": False,
            "account_id": self.company_data["default_account_receivable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -1050.0,
            "price_subtotal": -1050.0,
            "price_total": -1050.0,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1050.0,
            "debit": 1050.0,
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
            "amount_tax": 50.0,
            "amount_total": 1050.0,
        }

        self.assertInvoiceValues(
            self.move_out_venda,
            [
                product_line_vals_1,
                tax_line_vals_cofins,
                tax_line_vals_icms,
                tax_line_vals_ipi,
                tax_line_vals_pis,
                term_line_vals_1,
            ],
            move_vals,
        )

    def test_venda_with_icms_reduction(self):
        product_line_vals_1 = {
            "name": self.product_a.name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1050.00,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -875.38,
            "debit": 0.0,
            "credit": 875.38,
            "date_maturity": False,
        }

        tax_line_vals_cofins = {
            "name": "COFINS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 30.0,
            "price_subtotal": 30.0,
            "price_total": 30.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS Saida")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -30.0,
            "debit": 0.0,
            "credit": 30.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 88.12,
            "price_subtotal": 88.12,
            "price_total": 88.12,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -88.12,
            "debit": 0.0,
            "credit": 88.12,
            "date_maturity": False,
        }

        tax_line_vals_ipi = {
            "name": "IPI Saída",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "IPI a Recolher"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                order="id ASC",
                limit=1,
            )
            .id,  # TODO find our why this complex domain is required for IPI
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 50.0,
            "price_subtotal": 50.0,
            "price_total": 50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Saída")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
        }

        tax_line_vals_pis = {
            "name": "PIS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 6.5,
            "price_subtotal": 6.5,
            "price_total": 6.5,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "",
            "product_id": False,
            "account_id": self.company_data["default_account_receivable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -1050.00,
            "price_subtotal": -1050.00,
            "price_total": -1050.00,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1050.00,
            "debit": 1050.00,
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
            "amount_tax": 50.0,
            "amount_total": 1050.0,
        }

        self.assertInvoiceValues(
            self.move_out_venda_with_icms_reduction,
            [
                product_line_vals_1,
                tax_line_vals_cofins,
                tax_line_vals_icms,
                tax_line_vals_ipi,
                tax_line_vals_pis,
                term_line_vals_1,
            ],
            move_vals,
        )

    def test_venda_with_icms_reduction_with_relief(self):
        # Testando com Alivio do ICMS
        self.move_out_venda_with_icms_reduction.invoice_line_ids[0].icms_relief_id = 1
        self.move_out_venda_with_icms_reduction.invoice_line_ids._onchange_fiscal_taxes()
        self.move_out_venda_with_icms_reduction.line_ids._compute_amounts()
        self.move_out_venda_with_icms_reduction.invoice_line_ids.with_context(
            check_move_validity=False
        )._onchange_price_subtotal()
        self.move_out_venda_with_icms_reduction.with_context(
            check_move_validity=False
        )._recompute_dynamic_lines(recompute_all_taxes=True)
        self.move_out_venda_with_icms_reduction.line_ids._onchange_price_subtotal()
        self.move_out_venda_with_icms_reduction._check_balanced()

        product_line_vals_1 = {
            "name": self.product_a.name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1013.77,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -839.15,
            "debit": 0.0,
            "credit": 839.15,
            "date_maturity": False,
        }

        tax_line_vals_cofins = {
            "name": "COFINS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 30.0,
            "price_subtotal": 30.0,
            "price_total": 30.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS Saida")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -30.0,
            "debit": 0.0,
            "credit": 30.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 88.12,
            "price_subtotal": 88.12,
            "price_total": 88.12,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -88.12,
            "debit": 0.0,
            "credit": 88.12,
            "date_maturity": False,
        }

        tax_line_vals_ipi = {
            "name": "IPI Saída",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "IPI a Recolher"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                order="id ASC",
                limit=1,
            )
            .id,  # TODO find our why this complex domain is required for IPI
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 50.0,
            "price_subtotal": 50.0,
            "price_total": 50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Saída")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
        }

        tax_line_vals_pis = {
            "name": "PIS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 6.5,
            "price_subtotal": 6.5,
            "price_total": 6.5,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "",
            "product_id": False,
            "account_id": self.company_data["default_account_receivable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -1013.77,
            "price_subtotal": -1013.77,
            "price_total": -1013.77,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1013.77,
            "debit": 1013.77,
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
            "amount_tax": 50.0,
            "amount_total": 1013.77,
        }

        self.assertInvoiceValues(
            self.move_out_venda_with_icms_reduction,
            [
                product_line_vals_1,
                tax_line_vals_cofins,
                tax_line_vals_icms,
                tax_line_vals_ipi,
                tax_line_vals_pis,
                term_line_vals_1,
            ],
            move_vals,
        )

    def test_simples_remessa(self):
        product_line_vals_1 = {
            "name": self.product_a.name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1050.0,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 0.0,
            "debit": 0.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_cofins = {
            "name": "COFINS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 30.0,
            "price_subtotal": 30.0,
            "price_total": 30.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS Saida")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -30.0,
            "debit": 0.0,
            "credit": 30.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 120.0,
            "price_subtotal": 120.0,
            "price_total": 120.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
        }

        tax_line_vals_ipi = {
            "name": "IPI Saída",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "IPI a Recolher"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                order="id ASC",
                limit=1,
            )
            .id,  # TODO find our why this complex domain is required for IPI
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 50.0,
            "price_subtotal": 50.0,
            "price_total": 50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Saída")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
        }

        tax_line_vals_pis = {
            "name": "PIS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 6.5,
            "price_subtotal": 6.5,
            "price_total": 6.5,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "",
            "product_id": False,
            "account_id": self.company_data["default_account_receivable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -206.5,
            "price_subtotal": -206.5,
            "price_total": -206.5,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 206.5,
            "debit": 206.5,
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
            "amount_untaxed": 1000.0,  # FIXME is this correct for a simples remessa??
            "amount_tax": 50.0,
            "amount_total": 206.5,
        }

        self.assertInvoiceValues(
            self.move_out_simples_remessa,
            [
                product_line_vals_1,
                tax_line_vals_cofins,
                tax_line_vals_icms,
                tax_line_vals_ipi,
                tax_line_vals_pis,
                term_line_vals_1,
            ],
            move_vals,
        )

    def test_compra_para_revenda(self):
        """
        Test move with deductible taxes
        """
        product_line_vals_1 = {
            "name": self.product_a.name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_expense_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1050.0,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1050.0,
            "debit": 1050.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_cofins = {
            "name": "COFINS Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 30.0,
            "price_subtotal": 30.0,
            "price_total": 30.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS Entrada")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 30.0,
            "debit": 30.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_cofins_comp = {
            "name": "COFINS Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -30.0,
            "price_subtotal": -30.0,
            "price_total": -30.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search(
                [("name", "=", "COFINS Entrada Dedutível")], order="id desc", limit=1
            )
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -30.0,
            "debit": 0.0,
            "credit": 30.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 120.0,
            "price_subtotal": 120.0,
            "price_total": 120.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Entrada")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 120.0,
            "debit": 120.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_icms_comp = {
            "name": "ICMS Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -120.0,
            "price_subtotal": -120.0,
            "price_total": -120.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Entrada Dedutível")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
        }

        tax_line_vals_ipi = {
            "name": "IPI Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "IPI a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 50.0,
            "price_subtotal": 50.0,
            "price_total": 50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Entrada")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 50.0,
            "debit": 50.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_ipi_comp = {
            "name": "IPI Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "IPI s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -50.0,
            "price_subtotal": -50.0,
            "price_total": -50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Entrada Dedutível")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
        }

        tax_line_vals_pis = {
            "name": "PIS Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 6.5,
            "price_subtotal": 6.5,
            "price_total": 6.5,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Entrada")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 6.5,
            "debit": 6.5,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_pis_comp = {
            "name": "PIS Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -6.5,
            "price_subtotal": -6.5,
            "price_total": -6.5,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Entrada Dedutível")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "42/1-1",
            "product_id": False,
            "account_id": self.company_data["default_account_payable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -1050.0,
            "price_subtotal": -1050.0,
            "price_total": -1050.0,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -1050.0,
            "debit": 0.0,
            "credit": 1050.0,
            "date_maturity": fields.Date.from_string("2019-01-01"),
        }

        move_vals = {
            "partner_id": self.partner_a.id,
            "currency_id": self.company_data["currency"].id,
            "journal_id": self.company_data["default_journal_purchase"].id,
            "date": fields.Date.from_string("2019-01-01"),
            "fiscal_position_id": False,
            "payment_reference": "",
            "invoice_payment_term_id": self.pay_terms_a.id,
            "amount_untaxed": 1000.0,
            "amount_tax": 50.0,
            "amount_total": 1050.0,
        }

        self.assertInvoiceValues(
            self.move_in_compra_para_revenda,
            [
                product_line_vals_1,
                tax_line_vals_cofins,
                tax_line_vals_cofins_comp,
                tax_line_vals_icms,
                tax_line_vals_icms_comp,
                tax_line_vals_ipi,
                tax_line_vals_ipi_comp,
                tax_line_vals_pis,
                tax_line_vals_pis_comp,
                term_line_vals_1,
            ],
            move_vals,
        )

    # TODO test effect of ind_final?
    # ver aqui https://github.com/OCA/l10n-brazil/pull/2347#issuecomment-1548345563

    # Tax Withholding Tests
    def test_venda_tax_withholding(self):
        product_line_vals_1 = {
            "name": self.product_a.name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1050.0,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -880.0,
            "debit": 0.0,
            "credit": 880.0,
            "date_maturity": False,
        }

        tax_line_vals_cofins = {
            "name": "COFINS WH Saida",
            "product_id": False,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -30.0,
            "price_subtotal": -30.0,
            "price_total": -30.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS WH Saida")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 30.0,
            "debit": 30.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 120.0,
            "price_subtotal": 120.0,
            "price_total": 120.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
        }

        tax_line_vals_ipi = {
            "name": "IPI Saída",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "IPI a Recolher"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                order="id ASC",
                limit=1,
            )
            .id,  # TODO find our why this complex domain is required for IPI
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 50.0,
            "price_subtotal": 50.0,
            "price_total": 50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Saída")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
        }

        tax_line_vals_pis = {
            "name": "PIS WH Saida",
            "product_id": False,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -6.5,
            "price_subtotal": -6.5,
            "price_total": -6.5,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS WH Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 6.5,
            "debit": 6.5,
            "credit": 0.0,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "",
            "product_id": False,
            "account_id": self.company_data["default_account_receivable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -1013.5,
            "price_subtotal": -1013.5,
            "price_total": -1013.5,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1013.5,
            "debit": 1013.5,
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
            "amount_tax": 50.0,
            "amount_total": 1013.5,
        }

        self.assertInvoiceValues(
            self.move_out_venda_tax_withholding,
            [
                product_line_vals_1,
                tax_line_vals_cofins,
                tax_line_vals_icms,
                tax_line_vals_ipi,
                tax_line_vals_pis,
                term_line_vals_1,
            ],
            move_vals,
        )

    def test_simples_remessa_tax_withholding(self):
        product_line_vals_1 = {
            "name": self.product_a.name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1050.0,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 0.0,
            "debit": 0.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_cofins = {
            "name": "COFINS WH Saida",
            "product_id": False,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -30.0,
            "price_subtotal": -30.0,
            "price_total": -30.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS WH Saida")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 30.0,
            "debit": 30.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 120.0,
            "price_subtotal": 120.0,
            "price_total": 120.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
        }

        tax_line_vals_ipi = {
            "name": "IPI Saída",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "IPI a Recolher"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                order="id ASC",
                limit=1,
            )
            .id,  # TODO find our why this complex domain is required for IPI
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 50.0,
            "price_subtotal": 50.0,
            "price_total": 50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Saída")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
        }

        tax_line_vals_pis = {
            "name": "PIS WH Saida",
            "product_id": False,
            "account_id": self.product_a.property_account_income_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -6.5,
            "price_subtotal": -6.5,
            "price_total": -6.5,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS WH Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 6.5,
            "debit": 6.5,
            "credit": 0.0,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "",
            "product_id": False,
            "account_id": self.company_data["default_account_receivable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -133.5,
            "price_subtotal": -133.5,
            "price_total": -133.5,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 133.5,
            "debit": 133.5,
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
            "amount_untaxed": 1000.0,  # FIXME is this correct for a simples remessa??
            "amount_tax": 50.0,
            "amount_total": 133.5,
        }

        self.assertInvoiceValues(
            self.move_out_simples_remessa_tax_withholding,
            [
                product_line_vals_1,
                tax_line_vals_cofins,
                tax_line_vals_icms,
                tax_line_vals_ipi,
                tax_line_vals_pis,
                term_line_vals_1,
            ],
            move_vals,
        )

    def test_compra_para_revenda_tax_withholding(self):
        """
        Test move with deductible taxes and tax withholding
        """
        product_line_vals_1 = {
            "name": self.product_a.name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_expense_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1050.0,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1050.0,
            "debit": 1050.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_cofins = {
            "name": "COFINS WH Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -30.0,
            "price_subtotal": -30.0,
            "price_total": -30.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS WH Entrada")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -30.0,
            "debit": 0.0,
            "credit": 30.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 120.0,
            "price_subtotal": 120.0,
            "price_total": 120.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Entrada")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 120.0,
            "debit": 120.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_icms_comp = {
            "name": "ICMS Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -120.0,
            "price_subtotal": -120.0,
            "price_total": -120.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Entrada Dedutível")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
        }

        tax_line_vals_ipi = {
            "name": "IPI Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "IPI a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 50.0,
            "price_subtotal": 50.0,
            "price_total": 50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Entrada")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 50.0,
            "debit": 50.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_ipi_comp = {
            "name": "IPI Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "IPI s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -50.0,
            "price_subtotal": -50.0,
            "price_total": -50.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Entrada Dedutível")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
        }

        tax_line_vals_pis = {
            "name": "PIS WH Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -6.5,
            "price_subtotal": -6.5,
            "price_total": -6.5,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS WH Entrada")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "44/1-1",
            "product_id": False,
            "account_id": self.company_data["default_account_payable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": -1013.5,
            "price_subtotal": -1013.5,
            "price_total": -1013.5,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -1013.5,
            "debit": 0.0,
            "credit": 1013.5,
            "date_maturity": fields.Date.from_string("2019-01-01"),
        }

        move_vals = {
            "partner_id": self.partner_a.id,
            "currency_id": self.company_data["currency"].id,
            "journal_id": self.company_data["default_journal_purchase"].id,
            "date": fields.Date.from_string("2019-01-01"),
            "fiscal_position_id": False,
            "payment_reference": "",
            "invoice_payment_term_id": self.pay_terms_a.id,
            "amount_untaxed": 1000.0,
            "amount_tax": 50.0,
            "amount_total": 1013.5,
        }

        self.assertInvoiceValues(
            self.move_in_compra_para_revenda_tax_withholding,
            [
                product_line_vals_1,
                tax_line_vals_cofins,
                tax_line_vals_icms,
                tax_line_vals_icms_comp,
                tax_line_vals_ipi,
                tax_line_vals_ipi_comp,
                tax_line_vals_pis,
                term_line_vals_1,
            ],
            move_vals,
        )

    def test_composite_move(self):
        # first we make a few assertions about an existing vendor bill:
        self.assertEqual(len(self.move_in_compra_para_revenda.invoice_line_ids), 1)
        self.assertEqual(len(self.move_in_compra_para_revenda.line_ids), 10)
        self.assertEqual(self.move_in_compra_para_revenda.amount_total, 1050)

        self.assertEqual(len(self.move_in_compra_para_revenda.fiscal_document_ids), 1)
        self.assertEqual(
            self.move_in_compra_para_revenda.open_fiscal_document()["res_id"],
            self.move_in_compra_para_revenda.fiscal_document_id.id,
        )

        # now we create a dumb fiscal document we will import in our vendor bill:
        fiscal_doc_to_import = self.env["l10n_br_fiscal.document"].create(
            {
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie": 1,
                "document_number": 123,
                "issuer": "partner",
                "partner_id": self.partner_a.id,
                "fiscal_operation_type": "in",
            }
        )

        fiscal_doc_line_to_import = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": fiscal_doc_to_import.id,
                "name": "Purchase Test",
                "product_id": self.product_a.id,
                "fiscal_operation_type": "in",
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_compras_compras"
                ).id,
            }
        )
        fiscal_doc_line_to_import._onchange_product_id_fiscal()

        # let's import it:
        self.move_in_compra_para_revenda.fiscal_document_id = fiscal_doc_to_import
        self.move_in_compra_para_revenda.button_import_fiscal_document()

        # now a few assertions to check if it has been properly imported:
        self.assertEqual(len(self.move_in_compra_para_revenda.invoice_line_ids), 2)
        self.assertEqual(
            self.move_in_compra_para_revenda.invoice_line_ids[
                1
            ].fiscal_document_line_id.product_id,
            self.product_a,
        )

        self.assertEqual(len(self.move_in_compra_para_revenda.fiscal_document_ids), 2)
        self.assertIn(
            str(fiscal_doc_to_import.id),
            str(self.move_in_compra_para_revenda.open_fiscal_document()["domain"]),
        )
        self.assertIn(
            str(self.move_in_compra_para_revenda.fiscal_document_id.id),
            str(self.move_in_compra_para_revenda.open_fiscal_document()["domain"]),
        )

        invoice_lines = sorted(
            self.move_in_compra_para_revenda.invoice_line_ids, key=lambda item: item.id
        )
        self.assertEqual(
            fiscal_doc_to_import.id,
            invoice_lines[1].fiscal_document_line_id.document_id.id,
        )
        self.assertEqual(len(self.move_in_compra_para_revenda.line_ids), 11)
        self.assertEqual(self.move_in_compra_para_revenda.amount_total, 2100)
