# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo.tests import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestPurchaseTaxCreditability(AccountMoveBRCommon):
    """A vendor bill books as tax to recover only what the creditability map of
    its fiscal line credits, when the company values its stock at the net cost.
    The tax it may not credit stays in the expense or in the asset."""

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        if company_name == "company_1_data":
            company_name = "empresa 1 creditabilidade"
            cnpj = "62.128.834/0001-34"
        else:
            company_name = "empresa 2 creditabilidade"
            cnpj = "87.396.251/0001-15"
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
        res["company"].partner_id.state_id = cls.env.ref("base.state_br_sp").id
        res["company"].partner_id.cnpj_cpf = cnpj
        chart_template.load_fiscal_taxes()
        return res

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()
        cls.company = cls.company_data["company"]
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.operation.with_company(cls.company).deductible_taxes = False
        cls.partner_a.fiscal_profile_id = cls.env.ref(
            "l10n_br_fiscal.partner_fiscal_profile_cnt"
        )
        cls._number = 7100

    def _opt_in(self, value=True):
        if "stock_valuation_via_stock_price" not in self.company._fields:
            self.skipTest("l10n_br_stock_account is not installed")
        self.company.stock_valuation_via_stock_price = value

    def _bill(self, operation_line):
        type(self)._number += 1
        move = self.init_invoice(
            "in_invoice",
            partner=self.partner_a,
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.operation,
            fiscal_operation_lines=[self.env.ref(f"l10n_br_fiscal.{operation_line}")],
            document_serie="1",
            document_number=str(self._number),
        )
        move.action_post()
        return move

    @staticmethod
    def _product_line(move):
        return move.invoice_line_ids.filtered("product_id")

    @staticmethod
    def _tax_lines(move, domain):
        return move.line_ids.filtered(
            lambda line: line.tax_line_id.tax_group_id.fiscal_tax_group_id.tax_domain
            == domain
        )

    def _assert_tax_in_cost(self, operation_line, cfops):
        self._opt_in()
        move = self._bill(operation_line)
        line = self._product_line(move)
        self.assertIn(line.cfop_id.code, cfops)
        self.assertGreater(line.icms_value, 0, "the note has ICMS")
        self.assertGreater(line.ipi_value, 0, "the note has IPI")
        self.assertFalse(self._tax_lines(move, "icms"), "no ICMS to recover")
        self.assertFalse(self._tax_lines(move, "ipi"), "no IPI to recover")
        self.assertAlmostEqual(line.balance, line.fiscal_amount_total, places=2)
        self.assertAlmostEqual(line.balance, move.amount_total, places=2)

    def test_use_and_consumption_keeps_icms_and_ipi_in_the_expense(self):
        self._assert_tax_in_cost("fo_compras_compras_uso_consumo", ("1556", "2556"))

    def test_fixed_asset_keeps_icms_and_ipi_in_the_asset(self):
        self._assert_tax_in_cost("fo_compras_compras_ativo", ("1551", "2551"))

    def test_resale_keeps_icms_and_ipi_to_recover(self):
        self._opt_in()
        move = self._bill("fo_compras_compras_comercializacao")
        line = self._product_line(move)
        icms = self._tax_lines(move, "icms")
        ipi = self._tax_lines(move, "ipi")
        self.assertAlmostEqual(sum(icms.mapped("balance")), line.icms_value, places=2)
        self.assertAlmostEqual(sum(ipi.mapped("balance")), line.ipi_value, places=2)
        # presumed profit: PIS and COFINS are not a credit
        self.assertFalse(self._tax_lines(move, "pis"))
        self.assertFalse(self._tax_lines(move, "cofins"))
        self.assertAlmostEqual(
            line.balance,
            line.fiscal_amount_total - line.icms_value - line.ipi_value,
            places=2,
        )

    def test_a_company_that_did_not_opt_in_keeps_its_ledger(self):
        self._opt_in(False)
        move = self._bill("fo_compras_compras_uso_consumo")
        line = self._product_line(move)
        icms = self._tax_lines(move, "icms")
        ipi = self._tax_lines(move, "ipi")
        self.assertAlmostEqual(sum(icms.mapped("balance")), line.icms_value, places=2)
        self.assertAlmostEqual(sum(ipi.mapped("balance")), line.ipi_value, places=2)
        self.assertAlmostEqual(
            line.balance,
            line.fiscal_amount_total
            - line.amount_tax_included
            - line.amount_tax_not_included,
            places=2,
        )
