# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDraDva(AccountTestInvoicingCommon):
    # Pin the core generic chart for the test companies, as in the tests of
    # l10n_br_mis_report: the full CI database would otherwise pick br_oca
    # and install l10n_br_account in the middle of the tests.
    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.journal = cls.company_data["default_journal_misc"]
        cls.dra = cls.env.ref("l10n_br_mis_report_sa.dra")
        cls.dva = cls.env.ref("l10n_br_mis_report_sa.dva")

        def account(code, name, account_type, *tags):
            return cls.env["account.account"].create(
                {
                    "code": code,
                    "name": name,
                    "account_type": account_type,
                    "tag_ids": [
                        (4, cls.env.ref(f"l10n_br_coa.{tag}").id) for tag in tags
                    ],
                }
            )

        cls.caixa = account(
            "DVA10",
            "Caixa",
            "asset_cash",
            "account_tag_current_assets_cash",
            "account_tag_cash_and_equivalents",
        )
        cls.deprec_acum = account(
            "DVA14",
            "Depreciação Acumulada",
            "asset_fixed",
            "account_tag_fixed_assets_depreciation",
            "account_tag_cash_flow_result_adjustment",
        )
        cls.ajuste_pl = account(
            "DVA24",
            "Ajustes de Avaliação Patrimonial",
            "equity",
            "account_tag_equity_valuation_adjustment",
            "account_tag_cash_flow_non_cash",
        )
        cls.receita = account(
            "DVA90",
            "Vendas",
            "income",
            "account_tag_revenue",
            "account_tag_result",
        )
        cls.insumo = account(
            "DVA91",
            "Energia Elétrica",
            "expense",
            "account_tag_admin_expenses",
            "account_tag_result",
            "account_tag_dva_inputs",
        )
        cls.salario = account(
            "DVA92",
            "Salários",
            "expense",
            "account_tag_other_general_expenses",
            "account_tag_result",
            "account_tag_dva_personnel",
        )
        cls.imposto = account(
            "DVA93",
            "IPTU",
            "expense",
            "account_tag_other_general_expenses",
            "account_tag_result",
            "account_tag_dva_taxes",
            "account_tag_dva_taxes_municipal",
        )
        cls.juros = account(
            "DVA94",
            "Juros Passivos",
            "expense",
            "account_tag_expenses_financial",
            "account_tag_result",
            "account_tag_dva_third_party_capital",
        )
        cls.despesa_deprec = account(
            "DVA95",
            "Depreciação",
            "expense",
            "account_tag_other_general_expenses",
            "account_tag_result",
            "account_tag_depreciation_expense",
        )
        cls.receita_financeira = account(
            "DVA96",
            "Rendimentos de Aplicações",
            "income_other",
            "account_tag_revenue_financial",
            "account_tag_result",
            "account_tag_dva_transfer",
        )
        cls.oci_hedge = account(
            "DVA97",
            "Hedge de Fluxo de Caixa",
            "income_other",
            "account_tag_oci_hedge",
            "account_tag_result",
            "account_tag_dva_inputs",
        )

        cls.devolucao = account(
            "DVA98",
            "Devolução de Vendas",
            "income_other",
            "account_tag_revenue_deduction",
            "account_tag_result",
        )
        cls.icms_vendas = account(
            "DVA99",
            "ICMS sobre Vendas",
            "income_other",
            "account_tag_revenue_deduction",
            "account_tag_result",
            "account_tag_dva_taxes",
            "account_tag_dva_taxes_state",
        )

        cls.date_from = "2026-01-01"
        cls.date_to = "2026-12-31"

    @classmethod
    def _post(cls, lines, date="2026-06-15"):
        move = cls.env["account.move"].create(
            {
                "journal_id": cls.journal.id,
                "company_id": cls.company.id,
                "date": date,
                "line_ids": [
                    (0, 0, {"account_id": acc.id, "debit": d, "credit": c})
                    for acc, d, c in lines
                ],
            }
        )
        move.action_post()
        return move

    def _evaluate(self, report):
        aep = report._prepare_aep(self.company)
        return report.with_company(self.company).evaluate(
            aep, date_from=self.date_from, date_to=self.date_to
        )

    def _movimento_completo(self):
        """A year that touches every line of the distribution."""
        self._post([(self.caixa, 10000.0, 0.0), (self.receita, 0.0, 10000.0)])
        self._post([(self.insumo, 1500.0, 0.0), (self.caixa, 0.0, 1500.0)])
        self._post([(self.salario, 2500.0, 0.0), (self.caixa, 0.0, 2500.0)])
        self._post([(self.imposto, 700.0, 0.0), (self.caixa, 0.0, 700.0)])
        self._post([(self.juros, 400.0, 0.0), (self.caixa, 0.0, 400.0)])
        self._post([(self.despesa_deprec, 600.0, 0.0), (self.deprec_acum, 0.0, 600.0)])
        self._post([(self.caixa, 300.0, 0.0), (self.receita_financeira, 0.0, 300.0)])

    def test_the_value_added_distributed_equals_the_value_added_to_distribute(self):
        """It only holds if every result account is classified exactly once."""
        self._movimento_completo()
        r = self._evaluate(self.dva)
        self.assertAlmostEqual(
            r["valor_distribuir"],
            r["distribuido"],
            places=2,
            msg=f"{r['valor_distribuir']:.2f} to distribute, "
            f"{r['distribuido']:.2f} distributed",
        )

    def test_each_line_of_the_value_added_carries_its_own_nature(self):
        """The same expense lands where the CPC 09 puts it, not where the DRE does."""
        self._movimento_completo()
        r = self._evaluate(self.dva)
        self.assertAlmostEqual(r["vendas"], 10000.0, places=2)
        self.assertAlmostEqual(r["insumos"], 1500.0, places=2)
        self.assertAlmostEqual(r["depreciacao"], 600.0, places=2)
        self.assertAlmostEqual(r["transferencia"], 300.0, places=2)
        self.assertAlmostEqual(r["pessoal"], 2500.0, places=2)
        self.assertAlmostEqual(r["impostos"], 700.0, places=2)
        self.assertAlmostEqual(r["terceiros"], 400.0, places=2)
        self.assertAlmostEqual(r["valor_distribuir"], 8200.0, places=2)
        self.assertAlmostEqual(r["proprios"], 4600.0, places=2)

    def test_depreciation_is_not_counted_as_an_input(self):
        """It has a line of its own, so it must not also count as an input."""
        self._post([(self.caixa, 5000.0, 0.0), (self.receita, 0.0, 5000.0)])
        self._post([(self.despesa_deprec, 800.0, 0.0), (self.deprec_acum, 0.0, 800.0)])
        r = self._evaluate(self.dva)
        self.assertAlmostEqual(r["insumos"], 0.0, places=2)
        self.assertAlmostEqual(r["depreciacao"], 800.0, places=2)
        self.assertAlmostEqual(r["valor_distribuir"], 4200.0, places=2)
        self.assertAlmostEqual(r["valor_distribuir"], r["distribuido"], places=2)

    def test_taxes_are_broken_down_by_sphere(self):
        """The CPC 09 model wants the tax distribution split by government level."""
        self._movimento_completo()
        r = self._evaluate(self.dva)
        self.assertAlmostEqual(r["impostos_municipais"], 700.0, places=2)
        self.assertAlmostEqual(r["impostos_estaduais"], 0.0, places=2)
        self.assertAlmostEqual(r["impostos_federais"], 0.0, places=2)

    def test_comprehensive_income_starts_where_the_income_statement_ends(self):
        """The net result is the first line, other comprehensive income adds to it."""
        self._post([(self.caixa, 4000.0, 0.0), (self.receita, 0.0, 4000.0)])
        self._post([(self.salario, 1000.0, 0.0), (self.caixa, 0.0, 1000.0)])
        r = self._evaluate(self.dra)
        self.assertAlmostEqual(r["resultado"], 3000.0, places=2)
        self.assertAlmostEqual(r["total_oci"], 0.0, places=2)
        self.assertAlmostEqual(r["abrangente"], 3000.0, places=2)

    def test_other_comprehensive_income_adds_to_the_result(self):
        """A hedge gain is recognised in equity, not in the result of the year."""
        self._post([(self.caixa, 4000.0, 0.0), (self.receita, 0.0, 4000.0)])
        self._post([(self.ajuste_pl, 900.0, 0.0), (self.oci_hedge, 0.0, 900.0)])
        r = self._evaluate(self.dra)
        self.assertAlmostEqual(r["hedge"], 900.0, places=2)
        self.assertAlmostEqual(r["abrangente"], r["resultado"] + 900.0, places=2)

    def test_a_sales_return_reduces_the_sales_line(self):
        """Returns reduce item 1.1, taxes on sales are distributed (CPC 09).

        A return reduces the result, so it has to reduce the sales line as
        well, or the value distributed falls short of the value to distribute.
        The tax on the sale stays in the sales line and is distributed in 8.2.
        """
        self._post([(self.caixa, 10000.0, 0.0), (self.receita, 0.0, 10000.0)])
        self._post([(self.devolucao, 1000.0, 0.0), (self.caixa, 0.0, 1000.0)])
        self._post([(self.icms_vendas, 1200.0, 0.0), (self.caixa, 0.0, 1200.0)])
        r = self._evaluate(self.dva)
        self.assertAlmostEqual(r["vendas"], 9000.0, places=2)
        self.assertAlmostEqual(r["impostos"], 1200.0, places=2)
        self.assertAlmostEqual(r["impostos_estaduais"], 1200.0, places=2)
        self.assertAlmostEqual(r["proprios"], 7800.0, places=2)
        self.assertAlmostEqual(r["valor_distribuir"], r["distribuido"], places=2)
