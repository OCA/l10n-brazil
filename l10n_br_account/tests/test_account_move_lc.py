# Copyright 2023 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class AccountMoveLucroPresumido(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pis_tax_definition_empresa_lc = cls.env[
            "l10n_br_fiscal.tax.definition"
        ].create(
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

        cls.cofins_tax_definition_empresa_lc = cls.env[
            "l10n_br_fiscal.tax.definition"
        ].create(
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

        cls.empresa_lc_document_55_serie_1 = cls.env[
            "l10n_br_fiscal.document.serie"
        ].create(
            {
                "code": "1",
                "name": "Série 1",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "active": True,
            }
        )

        cls.move_out_venda = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
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
        self.product_line_vals_1 = {
            "name": self.product_a.name,
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
            "amount_currency": -843.5,
            "debit": 0.0,
            "credit": 843.5,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_cofins = {
            "name": "COFINS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS Saida")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -30.0,
            "debit": 0.0,
            "credit": 30.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_icms = {
            "name": "ICMS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_ipi = {
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
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Saída")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_pis = {
            "name": "PIS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.term_line_vals_1 = {
            "name": "",
            "product_id": False,
            "account_id": self.company_data["default_account_receivable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1050.0,
            "debit": 1050.0,
            "credit": 0.0,
            "date_maturity": fields.Date.from_string("2019-01-01"),
            "tax_exigible": True,
        }

        self.move_vals = {
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
                {
                    **self.product_line_vals_1,
                },
                {
                    **self.tax_line_vals_cofins,
                },
                {
                    **self.tax_line_vals_icms,
                },
                {
                    **self.tax_line_vals_ipi,
                },
                {
                    **self.tax_line_vals_pis,
                },
                {
                    **self.term_line_vals_1,
                },
            ],
            {
                **self.move_vals,
            },
        )

    def test_simples_remessa(self):
        self.product_line_vals_1 = {
            "name": self.product_a.name,
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
            "amount_currency": 0.0,
            "debit": 0.0,
            "credit": 0.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_cofins = {
            "name": "COFINS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS Saida")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -30.0,
            "debit": 0.0,
            "credit": 30.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_icms = {
            "name": "ICMS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_ipi = {
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
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Saída")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_pis = {
            "name": "PIS Saida",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS a Recolher")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Saida")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.term_line_vals_1 = {
            "name": "",
            "product_id": False,
            "account_id": self.company_data["default_account_receivable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 206.5,
            "debit": 206.5,
            "credit": 0.0,
            "date_maturity": fields.Date.from_string("2019-01-01"),
            "tax_exigible": True,
        }

        self.move_vals = {
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
                {
                    **self.product_line_vals_1,
                },
                {
                    **self.tax_line_vals_cofins,
                },
                {
                    **self.tax_line_vals_icms,
                },
                {
                    **self.tax_line_vals_ipi,
                },
                {
                    **self.tax_line_vals_pis,
                },
                {
                    **self.term_line_vals_1,
                },
            ],
            {
                **self.move_vals,
            },
        )

    def test_compra_para_revenda(self):
        """
        Test move with deductible taxes
        """
        self.product_line_vals_1 = {
            "name": self.product_a.name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_expense_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1000.0,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1050.0,
            "debit": 1050.0,
            "credit": 0.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_cofins = {
            "name": "COFINS Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "COFINS Entrada")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 30.0,
            "debit": 30.0,
            "credit": 0.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_cofins_comp = {
            "name": "COFINS Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "COFINS s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
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
            "tax_exigible": True,
        }

        self.tax_line_vals_icms = {
            "name": "ICMS Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Entrada")], order="id DESC", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 120.0,
            "debit": 120.0,
            "credit": 0.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_icms_comp = {
            "name": "ICMS Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "ICMS s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "ICMS Entrada Dedutível")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_ipi = {
            "name": "IPI Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "IPI a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Entrada")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 50.0,
            "debit": 50.0,
            "credit": 0.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_ipi_comp = {
            "name": "IPI Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "IPI s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "IPI Entrada Dedutível")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -50.0,
            "debit": 0.0,
            "credit": 50.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_pis = {
            "name": "PIS Entrada",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS a Compensar")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Entrada")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 6.5,
            "debit": 6.5,
            "credit": 0.0,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.tax_line_vals_pis_comp = {
            "name": "PIS Entrada Dedutível",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search([("name", "=", "PIS s/ Vendas")], order="id DESC", limit=1)
            .id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": self.env["account.tax"]
            .search([("name", "=", "PIS Entrada Dedutível")], order="id desc", limit=1)
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
            "tax_exigible": True,
        }

        self.term_line_vals_1 = {
            "name": "42/1-1",
            "product_id": False,
            "account_id": self.company_data["default_account_payable"].id,
            "partner_id": self.partner_a.id,
            "product_uom_id": False,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 0.0,
            "price_subtotal": 0.0,
            "price_total": 0.0,
            "tax_ids": [],
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -1050.0,
            "debit": 0.0,
            "credit": 1050.0,
            "date_maturity": fields.Date.from_string("2019-01-01"),
            "tax_exigible": True,
        }

        self.move_vals = {
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
                {
                    **self.product_line_vals_1,
                },
                {
                    **self.tax_line_vals_cofins,
                },
                {
                    **self.tax_line_vals_cofins_comp,
                },
                {
                    **self.tax_line_vals_icms,
                },
                {
                    **self.tax_line_vals_icms_comp,
                },
                {
                    **self.tax_line_vals_ipi,
                },
                {
                    **self.tax_line_vals_ipi_comp,
                },
                {
                    **self.tax_line_vals_pis,
                },
                {
                    **self.tax_line_vals_pis_comp,
                },
                {
                    **self.term_line_vals_1,
                },
            ],
            {
                **self.move_vals,
            },
        )

    # TODO test effect of ind_final?
    # ver aqui https://github.com/OCA/l10n-brazil/pull/2347#issuecomment-1548345563
