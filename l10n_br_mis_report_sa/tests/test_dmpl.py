# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""The statement of changes in equity has to tie, column by column.

Opening balance plus what moved has to equal the closing balance, on every
component, and the Total column has to reproduce the equity the balance sheet
shows on the same date. A matrix that renders and does not tie is wrong.
"""
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class EquityCommon(AccountTestInvoicingCommon):
    """Cenário compartilhado pela DMPL e pela DLPA.

    As duas leem os mesmos movimentos, e o que as faria divergir é justamente
    montar cenários separados para cada uma.
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.journal = cls.company_data["default_journal_misc"]
        cls.dmpl = cls.env.ref("l10n_br_mis_report_sa.dmpl")
        cls.bp = cls.env.ref("l10n_br_mis_report.bp")

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
            "DMP10", "Caixa", "asset_cash",
            "account_tag_current_assets_cash",
            "account_tag_cash_and_equivalents",
        )
        cls.capital = account(
            "DMP24", "Capital Social", "equity",
            "account_tag_equity_capital", "account_tag_cash_flow_financing",
        )
        cls.reserva = account(
            "DMP25", "Reserva Legal", "equity",
            "account_tag_equity_profit_reserve", "account_tag_cash_flow_non_cash",
        )
        cls.lucros = account(
            "DMP26", "Lucros Acumulados", "equity",
            "account_tag_equity_accumulated_profits",
            "account_tag_cash_flow_non_cash",
        )
        cls.dividendos = account(
            "DMP21", "Dividendos a Pagar", "liability_current",
            "account_tag_current_liabilities_payable",
            "account_tag_cash_flow_financing",
        )
        cls.receita = account(
            "DMP90", "Vendas", "income",
            "account_tag_revenue", "account_tag_result",
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

    def _column(self, values, kpi, index):
        """A matrix KPI comes back as one value per column, in order."""
        return values[kpi][index]


@tagged("post_install", "-at_install")
class TestDmpl(EquityCommon):
    def test_capital_paid_in_shows_on_its_own_column(self):
        """Paying in capital moves the capital column and nothing else."""
        self._post([(self.caixa, 20000.0, 0.0), (self.capital, 0.0, 20000.0)])
        r = self._evaluate(self.dmpl)
        # column order: capital, reservas de capital, reservas de lucros,
        # lucros acumulados, ajustes, total
        self.assertAlmostEqual(self._column(r, "aumento_capital", 0), 20000.0, places=2)
        self.assertAlmostEqual(self._column(r, "saldo_final", 0), 20000.0, places=2)
        self.assertAlmostEqual(self._column(r, "saldo_final", 5), 20000.0, places=2)

    def test_each_column_ties_from_opening_to_closing(self):
        """Opening plus movements equals closing, on every component."""
        self._post([(self.caixa, 20000.0, 0.0), (self.capital, 0.0, 20000.0)])
        self._post([(self.caixa, 7000.0, 0.0), (self.receita, 0.0, 7000.0)])
        self._post([(self.lucros, 1200.0, 0.0), (self.dividendos, 0.0, 1200.0)])
        self._post([(self.lucros, 800.0, 0.0), (self.reserva, 0.0, 800.0)])

        r = self._evaluate(self.dmpl)
        movimento_por_coluna = (
            "aumento_capital",
            "reducao_capital",
            "resultado",
            "abrangente",
            "reservas_movimento",
            "destinacao",
        )
        for index in range(6):
            inicial = self._column(r, "saldo_inicial", index)
            final = self._column(r, "saldo_final", index)
            movimentos = sum(
                self._column(r, kpi, index) for kpi in movimento_por_coluna
            )
            self.assertAlmostEqual(
                inicial + movimentos,
                final,
                places=2,
                msg="a coluna %s não fecha: %.2f de saldo inicial mais %.2f de "
                "movimento não dá os %.2f do saldo final"
                % (index, inicial, movimentos, final),
            )

    def test_the_total_column_reproduces_the_equity_of_the_balance_sheet(self):
        """The Total column is the equity the balance sheet shows.

        They are two statements reading the same thing, and a difference means
        one of them is leaving a component out.
        """
        self._post([(self.caixa, 20000.0, 0.0), (self.capital, 0.0, 20000.0)])
        self._post([(self.caixa, 7000.0, 0.0), (self.receita, 0.0, 7000.0)])
        self._post([(self.lucros, 1200.0, 0.0), (self.dividendos, 0.0, 1200.0)])

        dmpl = self._evaluate(self.dmpl)
        bp = self._evaluate(self.bp)
        self.assertAlmostEqual(
            self._column(dmpl, "saldo_final", 5),
            bp["patrimonio_liquido"],
            places=2,
        )

    def test_the_result_reaches_the_retained_earnings_column(self):
        """The result of the year lands on retained earnings, from the DRE.

        It is not on the account: the closing entry of the year is not booked,
        so the result lives on the result accounts. The statement reads it from
        the income statement, the same way the balance sheet does.
        """
        self._post([(self.caixa, 5000.0, 0.0), (self.receita, 0.0, 5000.0)])
        r = self._evaluate(self.dmpl)
        self.assertAlmostEqual(self._column(r, "resultado", 3), 5000.0, places=2)
        self.assertAlmostEqual(self._column(r, "saldo_final", 3), 5000.0, places=2)


@tagged("post_install", "-at_install")
class TestDlpa(EquityCommon):
    """The DLPA is the retained earnings column of the DMPL, shown as a list.

    It inherits the scenario of the DMPL on purpose: the two statements read
    the same movements, and reading them apart is what would let them drift.
    """

    def test_it_ties_and_agrees_with_the_dmpl(self):
        self._post([(self.caixa, 20000.0, 0.0), (self.capital, 0.0, 20000.0)])
        self._post([(self.caixa, 7000.0, 0.0), (self.receita, 0.0, 7000.0)])
        self._post([(self.lucros, 1200.0, 0.0), (self.dividendos, 0.0, 1200.0)])
        self._post([(self.lucros, 800.0, 0.0), (self.reserva, 0.0, 800.0)])

        dlpa = self._evaluate(self.env.ref("l10n_br_mis_report_sa.dlpa"))
        # it ties: what is at the disposal, less what was appropriated
        self.assertAlmostEqual(
            dlpa["disposicao"] + dlpa["reservas"] + dlpa["dividendos"],
            dlpa["saldo_final"],
            places=2,
        )
        # 7000 of result, less 800 to the reserve and 1200 to the shareholders
        self.assertAlmostEqual(dlpa["resultado"], 7000.0, places=2)
        self.assertAlmostEqual(dlpa["reservas"], -800.0, places=2)
        self.assertAlmostEqual(dlpa["dividendos"], -1200.0, places=2)
        self.assertAlmostEqual(dlpa["saldo_final"], 5000.0, places=2)

        # and it says the same as the retained earnings column of the DMPL
        dmpl = self._evaluate(self.dmpl)
        self.assertAlmostEqual(
            dlpa["saldo_final"], self._column(dmpl, "saldo_final", 3), places=2
        )
