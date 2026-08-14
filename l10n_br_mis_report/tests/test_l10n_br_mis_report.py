# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestL10nBrMisReport(AccountTestInvoicingCommon):
    """The reports are asserted against a posted entry, not against a fixture.

    The defect these tests exist for was invisible to any check that only
    looked at whether the report rendered: the balance sheet rendered fine and
    was off by the whole result of the year, because it had no line for it.
    """

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.bp = cls.env.ref("l10n_br_mis_report.bp")
        cls.dre = cls.env.ref("l10n_br_mis_report.dre")

        def account(code, name, account_type, tag, result=False):
            # a result account also carries the umbrella tag, the same way
            # the charts assign it: that is what the "Resultado do Exercicio"
            # line of the balance sheet selects
            tags = [(4, cls.env.ref("l10n_br_coa.%s" % tag).id)]
            if result:
                tags.append((4, cls.env.ref("l10n_br_coa.account_tag_result").id))
            return cls.env["account.account"].create(
                {
                    "code": code,
                    "name": name,
                    "account_type": account_type,
                    "company_id": cls.company.id,
                    "tag_ids": tags,
                }
            )

        cls.acc_caixa = account(
            "TSTCX", "Caixa", "asset_cash", "account_tag_current_assets_cash"
        )
        cls.acc_receita = account(
            "TSTRC", "Vendas", "income", "account_tag_revenue", result=True
        )
        cls.acc_despesa = account(
            "TSTDA",
            "Despesas Administrativas",
            "expense",
            "account_tag_admin_expenses",
            result=True,
        )
        cls.acc_capital = account(
            "TSTCP", "Capital Social", "equity", "account_tag_equity_capital"
        )

        cls.journal = cls.company_data["default_journal_misc"]
        # the closed financial year the tests work on
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

    def test_balance_sheet_closes_with_the_result_of_the_year(self):
        """Assets equal liabilities plus equity, with the year result between.

        A sale of 1000 collected in cash leaves 1000 in assets and 1000 of
        profit. Without the result line the equity side would read zero and
        the sheet would be off by 1000, which is the defect: on a real
        database the gap was the whole profit of the year.
        """
        self._post([(self.acc_caixa, 1000.0, 0.0), (self.acc_receita, 0.0, 1000.0)])
        r = self._evaluate(self.bp)
        self.assertAlmostEqual(r["total_ativo"], 1000.0, places=2)
        self.assertAlmostEqual(r["resultado_exercicio"], 1000.0, places=2)
        self.assertAlmostEqual(r["patrimonio_liquido"], 1000.0, places=2)
        self.assertAlmostEqual(r["total_passivo"], 1000.0, places=2)
        self.assertAlmostEqual(r["total_ativo"], r["total_passivo"], places=2)

    def test_balance_sheet_closes_with_capital_and_expenses(self):
        """The sheet also closes with paid-in capital and with a loss."""
        self._post([(self.acc_caixa, 5000.0, 0.0), (self.acc_capital, 0.0, 5000.0)])
        self._post([(self.acc_despesa, 800.0, 0.0), (self.acc_caixa, 0.0, 800.0)])
        r = self._evaluate(self.bp)
        # cash 5000 - 800 = 4200 of assets; capital 5000 and a loss of 800
        self.assertAlmostEqual(r["total_ativo"], 4200.0, places=2)
        self.assertAlmostEqual(r["capital_social"], 5000.0, places=2)
        self.assertAlmostEqual(r["resultado_exercicio"], -800.0, places=2)
        self.assertAlmostEqual(r["total_ativo"], r["total_passivo"], places=2)

    def test_income_statement_follows_the_legal_order(self):
        """The income statement walks down the steps article 187 lays out."""
        self._post([(self.acc_caixa, 1000.0, 0.0), (self.acc_receita, 0.0, 1000.0)])
        self._post([(self.acc_despesa, 250.0, 0.0), (self.acc_caixa, 0.0, 250.0)])
        r = self._evaluate(self.dre)
        self.assertAlmostEqual(r["receita_bruta"], 1000.0, places=2)
        self.assertAlmostEqual(r["receita_liquida"], 1000.0, places=2)
        self.assertAlmostEqual(r["lucro_bruto"], 1000.0, places=2)
        self.assertAlmostEqual(r["despesas_administrativas"], 250.0, places=2)
        self.assertAlmostEqual(r["resultado_operacional"], 750.0, places=2)
        self.assertAlmostEqual(r["resultado_liquido"], 750.0, places=2)

    def test_expenses_are_shown_positive_not_negative(self):
        """An expense reads positive on its line and negative in the subtotal.

        The sign convention is what separates a financial result added as
        revenue from one added as a cost; without it the pre-tax result comes
        out with the financial result inverted.
        """
        self._post([(self.acc_despesa, 400.0, 0.0), (self.acc_caixa, 0.0, 400.0)])
        r = self._evaluate(self.dre)
        self.assertAlmostEqual(r["despesas_administrativas"], 400.0, places=2)
        self.assertAlmostEqual(r["resultado_liquido"], -400.0, places=2)


@tagged("post_install", "-at_install")
class TestL10nBrMisReportPeriods(AccountTestInvoicingCommon):
    """The shipped periods have to yield the dates the law works with."""

    def _period(self, xmlid):
        return self.env.ref("l10n_br_mis_report.%s" % xmlid)

    def test_quarter_is_the_civil_quarter_of_the_assessment(self):
        """The income tax quarter is the civil one, not a three month window.

        With the base date anywhere inside the quarter, the column has to
        cover the whole quarter. A relative three month window would only
        coincide with it when the base date fell on the last month.
        """
        instance = self._period("instance_dre_trimestral")
        instance.date = fields.Date.to_date("2026-05-20")  # mid second quarter
        col = instance.period_ids.filtered(lambda p: p.offset == 0)
        self.assertEqual(str(col.date_from), "2026-04-01")
        self.assertEqual(str(col.date_to), "2026-06-30")

    def test_previous_quarter_and_same_quarter_last_year(self):
        instance = self._period("instance_dre_trimestral")
        instance.date = fields.Date.to_date("2026-05-20")
        anterior = instance.period_ids.filtered(lambda p: p.offset == -1)
        self.assertEqual(str(anterior.date_from), "2026-01-01")
        self.assertEqual(str(anterior.date_to), "2026-03-31")
        ano_anterior = instance.period_ids.filtered(lambda p: p.offset == -4)
        self.assertEqual(str(ano_anterior.date_from), "2025-04-01")
        self.assertEqual(str(ano_anterior.date_to), "2025-06-30")

    def test_year_to_date_column_starts_on_january_first(self):
        """The accumulated column runs from January 1st to the base month end."""
        instance = self._period("instance_dre_mensal")
        instance.date = fields.Date.to_date("2026-05-20")
        acumulado = instance.period_ids.filtered(lambda p: p.is_ytd and p.offset == 0)
        self.assertEqual(str(acumulado.date_from), "2026-01-01")
        self.assertEqual(str(acumulado.date_to), "2026-05-31")
        mes = instance.period_ids.filtered(lambda p: not p.is_ytd and p.offset == 0)
        self.assertEqual(str(mes.date_from), "2026-05-01")
        self.assertEqual(str(mes.date_to), "2026-05-31")

    def test_balance_sheet_columns_cover_whole_exercises(self):
        """The comparative sheet compares whole financial years.

        The column has to cover the year because the period result is read
        from the movement of the result accounts: on a shorter range the
        equity side would show only part of the profit.
        """
        instance = self._period("instance_bp_exercicio")
        instance.date = fields.Date.to_date("2026-05-20")
        atual = instance.period_ids.filtered(
            lambda p: p.source == "actuals" and p.offset == 0
        )
        self.assertEqual(str(atual.date_from), "2026-01-01")
        self.assertEqual(str(atual.date_to), "2026-12-31")
        anterior = instance.period_ids.filtered(
            lambda p: p.source == "actuals" and p.offset == -1
        )
        self.assertEqual(str(anterior.date_from), "2025-01-01")
        self.assertEqual(str(anterior.date_to), "2025-12-31")
