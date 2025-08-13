# Copyright 2024 Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class AccountMoveWithWhInvoice(AccountMoveBRCommon):
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
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_pis_wh_0_65").id,
                "state": "approved",
            }
        )

        cls.cofins_tax_definition_empresa_lc_wh_invoice = cls.env[
            "l10n_br_fiscal.tax.definition"
        ].create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_cofins").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_cofins_wh_3").id,
                "state": "approved",
            }
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
            document_number="54",
        )
        cls.env.ref("l10n_br_fiscal.tax_group_pis_wh").generate_wh_invoice = True
        cls.env.ref("l10n_br_fiscal.tax_group_cofins_wh").generate_wh_invoice = True

        cls.service_test = cls.env["product.product"].create(
            {
                "name": "Serviço de Testes",
                "type": "service",
                "standard_price": 1000.0,
                "tax_icms_or_issqn": "issqn",
                "ncm_id": cls.env.ref("l10n_br_fiscal.ncm_00000000").id,
                "fiscal_type": "09",
                "fiscal_genre_id": cls.env.ref("l10n_br_fiscal.product_genre_00").id,
                "service_type_id": cls.env.ref("l10n_br_fiscal.service_type_1009").id,
                "taxes_id": False,
            }
        )

        cls.test_partner = cls.env["res.partner"].create(
            {
                "name": "Test Company Brasil",
                "legal_name": "Test Company Brasil Ltda",
                "cnpj_cpf": "32.680.221/0001-44",
                "state_id": cls.env.ref("base.state_br_sp").id,
                "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
                "zip": "04576-060",
                "country_id": cls.env.ref("base.br").id,
                "inscr_est": "621.240.850.633",
                "is_company": True,
                "active": True,
            }
        )
        cls.test_partner._onchange_city_id()

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
            **kwargs,
        )
        res["company"].partner_id.state_id = cls.env.ref("base.state_br_sp")
        chart_template.load_fiscal_taxes()
        return res

    def test_compra_para_revenda(self):
        """
        Test move with deductible taxes and withholding taxes
        """
        product_line_vals_1 = {
            "name": self.product_a.display_name,
            "product_id": self.product_a.id,
            "account_id": self.product_a.property_account_expense_id.id,
            "partner_id": self.partner_a.id,
            "product_uom_id": self.product_a.uom_id.id,
            "quantity": 1.0,
            "discount": 0.0,
            "price_unit": 1000.0,
            "price_subtotal": 1000.0,
            "price_total": 1032.5,
            "tax_line_id": False,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 1032.5,
            "debit": 1032.5,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_cofins_wh = {
            "name": "COFINS RET",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "COFINS a Recolher"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
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
            .search(
                [
                    ("name", "=", "COFINS WH Entrada"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -30.0,
            "debit": 0.0,
            "credit": 30.0,
            "date_maturity": False,
        }

        tax_line_vals_icms_comp = {
            "name": "ICMS",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "ICMS s/ Vendas"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
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
            .search(
                [
                    ("name", "=", "ICMS Entrada Dedutível"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -120.0,
            "debit": 0.0,
            "credit": 120.0,
            "date_maturity": False,
        }

        tax_line_vals_icms = {
            "name": "ICMS",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "ICMS a Compensar"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
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
            .search(
                [
                    ("name", "=", "ICMS Entrada"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 120.0,
            "debit": 120.0,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_ipi_comp = {
            "name": "IPI",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "IPI s/ Vendas"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
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
            .search(
                [
                    ("name", "=", "IPI Entrada Dedutível"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -32.5,
            "debit": 0.0,
            "credit": 32.5,
            "date_maturity": False,
        }

        tax_line_vals_ipi = {
            "name": "IPI",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "IPI a Compensar"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
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
            .search(
                [
                    ("name", "=", "IPI Entrada"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": 32.5,
            "debit": 32.5,
            "credit": 0.0,
            "date_maturity": False,
        }

        tax_line_vals_pis_wh = {
            "name": "PIS RET",
            "product_id": False,
            "account_id": self.env["account.account"]
            .search(
                [
                    ("name", "=", "PIS a Recolher"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
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
            .search(
                [
                    ("name", "=", "PIS WH Entrada"),
                    ("company_id", "=", self.company_data["company"].id),
                ],
                limit=1,
            )
            .id,
            "currency_id": self.company_data["currency"].id,
            "amount_currency": -6.5,
            "debit": 0.0,
            "credit": 6.5,
            "date_maturity": False,
        }

        term_line_vals_1 = {
            "name": "54/1-1",
            "product_id": False,
            "account_id": self.company_data["default_account_payable"].id,
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
            "amount_currency": -996.0,
            "debit": 0.0,
            "credit": 996.0,
            "date_maturity": fields.Date.from_string("2019-01-01"),
        }

        move_vals = {
            "partner_id": self.partner_a.id,
            "currency_id": self.company_data["currency"].id,
            "journal_id": self.company_data["default_journal_purchase"].id,
            "date": fields.Date.from_string("2019-01-31"),
            "fiscal_position_id": False,
            "payment_reference": "",
            "invoice_payment_term_id": self.pay_terms_a.id,
            "amount_untaxed": 1000.0,
            "amount_tax": 32.5,
            "amount_total": 996.0,
        }

        self.assertInvoiceValues(
            self.move_in_compra_para_revenda,
            [
                product_line_vals_1,
                tax_line_vals_cofins_wh,
                tax_line_vals_icms_comp,
                tax_line_vals_icms,
                tax_line_vals_ipi_comp,
                tax_line_vals_ipi,
                tax_line_vals_pis_wh,
                term_line_vals_1,
            ],
            move_vals,
        )

        self.move_in_compra_para_revenda.action_post()
        self.move_in_compra_para_revenda._compute_wh_invoice_ids()
        self.assertEqual(
            self.move_in_compra_para_revenda.wh_invoice_count,
            2,
            "The invoice should have 2 withholding invoices (PIS and COFINS).",
        )

    def test_with_partner_issqn_without_city_partner(self):
        "Test move with Partner defined and no ISSQN City Partner"
        self.env.ref("l10n_br_fiscal.tax_group_pis_wh").generate_wh_invoice = False
        self.env.ref("l10n_br_fiscal.tax_group_cofins_wh").generate_wh_invoice = False
        product = self.service_test
        tax_group = self.env.ref("l10n_br_fiscal.tax_group_issqn_wh")
        tax_group.generate_wh_invoice = True
        tax_group.journal_id = self.company_data["default_journal_purchase"].id
        move_issqn = self.init_invoice(
            "in_invoice",
            products=[product],
            partner=self.test_partner,
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[self.env.ref("l10n_br_fiscal.fo_compras_servico")],
            document_serie="1",
            document_number="56",
        )

        for line_ids in move_issqn.invoice_line_ids:
            line_ids.issqn_tax_id = None
            line_ids.issqn_fg_city_id = self.env.ref("l10n_br_base.city_3550308")
            line_ids.issqn_wh_tax_id = self.env.ref("l10n_br_fiscal.tax_issqn_wh_5")

        move_issqn.invoice_line_ids._onchange_fiscal_taxes()
        move_issqn.action_post()
        move_issqn._compute_wh_invoice_ids()

        self.assertEqual(
            move_issqn.wh_invoice_count,
            1,
            "The invoice should have 1 withholding invoice (ISSQN).",
        )

        partner_wh = self.env["res.partner"].search(
            [
                ("city_id", "=", move_issqn.invoice_line_ids[0].issqn_fg_city_id.id),
                ("wh_cityhall", "=", True),
            ],
            limit=1,
        )

        expected_partner_id = partner_wh if partner_wh else tax_group.partner_id

        self.assertTrue(
            all(
                wh_inv.partner_id == expected_partner_id
                for wh_inv in move_issqn.wh_invoice_ids
            )
        )

    def test_with_partner_issqn_with_city_partner(self):
        "Test move with Partner and ISSQN City Partner"
        self.env.ref("l10n_br_fiscal.tax_group_pis_wh").generate_wh_invoice = False
        self.env.ref("l10n_br_fiscal.tax_group_cofins_wh").generate_wh_invoice = False
        product = self.service_test
        wh_payable_account = self.env["account.account"].create(
            {
                "name": "Withholding Payable",
                "code": "WHT210",
                "account_type": "liability_payable",
                "reconcile": True,
                "company_id": self.company_data["company"].id,
            }
        )

        tax_group = self.env.ref("l10n_br_fiscal.tax_group_issqn_wh")
        tax_group.write(
            {
                "generate_wh_invoice": True,
                "journal_id": self.company_data["default_journal_purchase"].id,
                "wh_payable_account_id": wh_payable_account.id,
            }
        )
        partner_cityhall = self.env["res.partner"].create(
            {
                "name": "Prefeitura de São Paulo",
                "city_id": self.env.ref("l10n_br_base.city_3550308").id,
                "state_id": self.env.ref("base.state_br_sp").id,
                "country_id": self.env.ref("base.br").id,
                "wh_cityhall": True,
            }
        )
        move_issqn = self.init_invoice(
            "in_invoice",
            products=[product],
            partner=partner_cityhall,
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[self.env.ref("l10n_br_fiscal.fo_compras_servico")],
            document_serie="1",
            document_number="56",
        )

        for line_ids in move_issqn.invoice_line_ids:
            line_ids.issqn_tax_id = None
            line_ids.issqn_fg_city_id = self.env.ref("l10n_br_base.city_3550308")
            line_ids.issqn_wh_tax_id = self.env.ref("l10n_br_fiscal.tax_issqn_wh_5")

        move_issqn.invoice_line_ids._onchange_fiscal_taxes()
        move_issqn.action_post()
        move_issqn._compute_wh_invoice_ids()

        self.assertEqual(
            move_issqn.wh_invoice_count,
            1,
            "The invoice should have 1 withholding invoice (ISSQN).",
        )
        self.assertTrue(
            all(
                wh_inv.partner_id == partner_cityhall
                for wh_inv in move_issqn.wh_invoice_ids
            )
        )
        payable_line_ids = move_issqn.wh_invoice_ids.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        self.assertTrue(
            all(
                pay_line.account_id == wh_payable_account
                for pay_line in payable_line_ids
            )
        )
