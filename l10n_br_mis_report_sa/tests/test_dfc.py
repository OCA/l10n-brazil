# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""The cash flow statement is a reconciliation, so it has to reconcile.

Every test here ends on the same assertion: the increase in cash the statement
arrives at equals the increase the cash accounts actually show. A statement
that renders beautifully and misses that equality is wrong, and no check that
only looks at whether the lines were drawn would notice.
"""
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDfc(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.journal = cls.company_data["default_journal_misc"]
        cls.dfc = cls.env.ref("l10n_br_mis_report_sa.dfc")

        def account(code, name, account_type, *tags):
            return cls.env["account.account"].create(
                {
                    "code": code,
                    "name": name,
                    "account_type": account_type,
                    "company_id": cls.company.id,
                    "tag_ids": [
                        (4, cls.env.ref("l10n_br_coa.%s" % tag).id) for tag in tags
                    ],
                }
            )

        cls.caixa = account(
            "DFC10", "Caixa", "asset_cash",
            "account_tag_current_assets_cash",
            "account_tag_cash_and_equivalents",
        )
        cls.clientes = account(
            "DFC12", "Clientes", "asset_receivable",
            "account_tag_current_assets_receivable",
            "account_tag_cash_flow_operating",
        )
        cls.fornecedores = account(
            "DFC21", "Fornecedores", "liability_payable",
            "account_tag_current_liabilities_suppliers",
            "account_tag_cash_flow_operating",
        )
        cls.imobilizado = account(
            "DFC13", "Imobilizado", "asset_fixed",
            "account_tag_fixed_assets",
            "account_tag_cash_flow_investing",
        )
        # a contrapartida do ajuste fica fora de qualquer soma: e o ajuste ao
        # resultado que a representa
        cls.deprec_acumulada = account(
            "DFC14", "Depreciação Acumulada", "asset_fixed",
            "account_tag_fixed_assets_depreciation",
            "account_tag_cash_flow_result_adjustment",
        )
        cls.emprestimo = account(
            "DFC22", "Empréstimos", "liability_current",
            "account_tag_current_liabilities_financial",
            "account_tag_cash_flow_financing",
        )
        cls.capital = account(
            "DFC24", "Capital Social", "equity",
            "account_tag_equity_capital",
            "account_tag_cash_flow_financing",
        )
        cls.lucros = account(
            "DFC25", "Lucros Acumulados", "equity",
            "account_tag_equity_accumulated_profits",
            "account_tag_cash_flow_non_cash",
        )
        cls.dividendos = account(
            "DFC26", "Dividendos a Pagar", "liability_current",
            "account_tag_current_liabilities_payable",
            "account_tag_cash_flow_financing",
        )
        cls.receita = account(
            "DFC90", "Vendas", "income",
            "account_tag_revenue", "account_tag_result",
        )
        cls.despesa = account(
            "DFC91", "Despesas Administrativas", "expense",
            "account_tag_admin_expenses", "account_tag_result",
        )
        cls.despesa_deprec = account(
            "DFC92", "Depreciação", "expense",
            "account_tag_other_general_expenses",
            "account_tag_result",
            "account_tag_depreciation_expense",
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

    def _evaluate(self):
        aep = self.dfc._prepare_aep(self.company)
        return self.dfc.with_company(self.company).evaluate(
            aep, date_from=self.date_from, date_to=self.date_to
        )

    def _assert_reconciles(self, r):
        self.assertAlmostEqual(
            r["variacao_caixa"],
            r["conferencia"],
            places=2,
            msg="a demonstração apurou %.2f de variação de caixa e as contas "
            "de caixa mostram %.2f" % (r["variacao_caixa"], r["conferencia"]),
        )

    def test_a_full_year_reconciles_with_the_cash_accounts(self):
        """Capital, sale on credit, collection, investment and depreciation.

        Cash: 10000 in from capital, 3000 collected, 4000 spent on the asset
        and 800 on the expense, so 8200. Every path through the statement has
        to land on that number.
        """
        self._post([(self.caixa, 10000.0, 0.0), (self.capital, 0.0, 10000.0)])
        self._post([(self.clientes, 5000.0, 0.0), (self.receita, 0.0, 5000.0)])
        self._post([(self.caixa, 3000.0, 0.0), (self.clientes, 0.0, 3000.0)])
        self._post([(self.imobilizado, 4000.0, 0.0), (self.caixa, 0.0, 4000.0)])
        self._post(
            [(self.despesa_deprec, 500.0, 0.0), (self.deprec_acumulada, 0.0, 500.0)]
        )
        self._post([(self.despesa, 800.0, 0.0), (self.caixa, 0.0, 800.0)])

        r = self._evaluate()
        self.assertAlmostEqual(r["conferencia"], 8200.0, places=2)
        self._assert_reconciles(r)
        # the result comes from the income statement, not recomputed here
        self.assertAlmostEqual(r["resultado"], 3700.0, places=2)
        # and depreciation is added back, since it consumed no cash
        self.assertAlmostEqual(r["depreciacao"], 500.0, places=2)
        self.assertAlmostEqual(r["resultado_ajustado"], 4200.0, places=2)

    def test_dividend_declaration_is_not_an_inflow_of_cash(self):
        """Appropriating profit moves nothing through the cash.

        It debits retained earnings and credits dividends payable. Without the
        line that isolates transactions with no cash, that credit would show up
        as an inflow in the financing activities, and the statement would claim
        cash that never came in.
        """
        self._post([(self.caixa, 10000.0, 0.0), (self.capital, 0.0, 10000.0)])
        self._post([(self.lucros, 1500.0, 0.0), (self.dividendos, 0.0, 1500.0)])

        r = self._evaluate()
        self.assertAlmostEqual(r["conferencia"], 10000.0, places=2)
        self._assert_reconciles(r)
        self.assertAlmostEqual(r["transacoes_sem_caixa"], -1500.0, places=2)

    def test_paying_the_dividend_is_an_outflow(self):
        """Paying it, on the other hand, is financing that leaves the cash."""
        self._post([(self.caixa, 10000.0, 0.0), (self.capital, 0.0, 10000.0)])
        self._post([(self.lucros, 1500.0, 0.0), (self.dividendos, 0.0, 1500.0)])
        self._post([(self.dividendos, 1500.0, 0.0), (self.caixa, 0.0, 1500.0)])

        r = self._evaluate()
        self.assertAlmostEqual(r["conferencia"], 8500.0, places=2)
        self._assert_reconciles(r)

    def test_a_loan_taken_and_partly_repaid_is_financing(self):
        self._post([(self.caixa, 6000.0, 0.0), (self.emprestimo, 0.0, 6000.0)])
        self._post([(self.emprestimo, 2000.0, 0.0), (self.caixa, 0.0, 2000.0)])

        r = self._evaluate()
        self.assertAlmostEqual(r["conferencia"], 4000.0, places=2)
        self.assertAlmostEqual(r["caixa_financiamento"], 4000.0, places=2)
        self._assert_reconciles(r)

    def test_buying_on_credit_from_a_supplier_generates_working_capital(self):
        """A purchase on credit funds itself: no cash leaves until it is paid."""
        self._post([(self.despesa, 900.0, 0.0), (self.fornecedores, 0.0, 900.0)])

        r = self._evaluate()
        self.assertAlmostEqual(r["conferencia"], 0.0, places=2)
        self._assert_reconciles(r)
        # the expense hit the result and the supplier gave it back
        self.assertAlmostEqual(r["resultado"], -900.0, places=2)
        self.assertAlmostEqual(r["variacao_operacional"], 900.0, places=2)
        self.assertAlmostEqual(r["caixa_operacional"], 0.0, places=2)
