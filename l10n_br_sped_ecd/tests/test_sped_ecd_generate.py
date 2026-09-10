# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Generation of block I from the Odoo ledger.

These tests assert VALUES, not presence. A register full of zeros passes any
check that only looks at whether the line was written, and is rejected by the
PVA all the same, so every assertion here names the amount it expects.
"""
from io import StringIO

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSpedEcdGenerate(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.journal = cls.company_data["default_journal_misc"]
        # the accountant of the account test common is not a fiscal manager,
        # and creating a declaration is a manager right
        cls.env.user.groups_id |= cls.env.ref("l10n_br_fiscal.group_manager")

        cls.group = cls.env["account.group"].create(
            {
                "name": "DISPONIVEL",
                "code_prefix_start": "ECD1",
                "company_id": cls.company.id,
            }
        )
        cls.acc_caixa = cls.env["account.account"].create(
            {
                "code": "ECD10",
                "name": "Caixa",
                "account_type": "asset_cash",
                "company_id": cls.company.id,
                "group_id": cls.group.id,
            }
        )
        cls.acc_receita = cls.env["account.account"].create(
            {
                "code": "ECD90",
                "name": "Vendas",
                "account_type": "income",
                "company_id": cls.company.id,
            }
        )

        cls.declaration = cls.env["l10n_br_sped.ecd.0000"].create(
            {
                "company_id": cls.company.id,
                "DT_INI": "2026-01-01",
                "DT_FIN": "2026-03-31",
                "LECD": "LECD",
                "NOME": cls.company.name,
                "CNPJ": "18751708000140",
                "UF": "SP",
                # the header fields the layout requires; the values are the
                # ordinary case: regular bookkeeping, not a consolidated nor a
                # centralised one, with no change of chart in the period
                "IND_SIT_INI_PER": "0",
                "IND_NIRE": "0",
                "IND_FIN_ESC": "0",
                "IND_GRANDE_PORTE": "N",
                "TIP_ECD": 0,
                "IDENT_MF": "N",
                "IND_ESC_CONS": "N",
                "IND_CENTRALIZADA": "0",
                "IND_MUDANC_PC": "0",
            }
        )

    @classmethod
    def _post(cls, date, amount):
        move = cls.env["account.move"].create(
            {
                "journal_id": cls.journal.id,
                "company_id": cls.company.id,
                "date": date,
                "line_ids": [
                    (0, 0, {"account_id": cls.acc_caixa.id, "debit": amount}),
                    (0, 0, {"account_id": cls.acc_receita.id, "credit": amount}),
                ],
            }
        )
        move.action_post()
        return move

    def _populate(self):
        """Pull the way `button_populate_sped_from_odoo` does.

        Block I hangs entirely under I010, so the pull starts there and
        cascades: pulling a child on its own would leave its parent link null.
        `default_declaration_id` is what ties each register created down the
        recursion to the declaration.
        """
        self.env["l10n_br_sped.ecd.i010"].with_context(
            company_id=self.company.id,
            declaration=self.declaration,
            default_declaration_id=self.declaration.id,
        )._pull_records_from_odoo("ecd", 2, log_msg=StringIO())

    def _registers(self, model_name):
        return self.env[model_name].search(
            [("declaration_id", "=", self.declaration.id)]
        )

    def test_entries_are_pulled_with_the_accounting_date_and_amount(self):
        """The entry carries its accounting date and the total of its debits.

        Two defects lived here: the domain filtered `state = "open"`, a value
        that does not exist in this version, so nothing was ever pulled; and
        the amount came from `fiscal_amount_total`, which is zero on every
        entry that did not come from a fiscal document.
        """
        self._post("2026-02-10", 1500.0)
        self._populate()
        registers = self._registers("l10n_br_sped.ecd.i200")
        self.assertEqual(len(registers), 1)
        self.assertEqual(str(registers.DT_LCTO), "2026-02-10")
        self.assertAlmostEqual(registers.VL_LCTO, 1500.0, places=2)

    def test_entries_on_the_period_edges_are_included(self):
        """The period bounds are inclusive.

        With the strict operator an entry booked on the first or the last day
        of the escrituracao was silently dropped.
        """
        self._post("2026-01-01", 100.0)
        self._post("2026-03-31", 200.0)
        self._populate()
        registers = self._registers("l10n_br_sped.ecd.i200")
        self.assertEqual(len(registers), 2)

    def test_line_amount_is_the_posted_value_not_the_currency_one(self):
        """A line carries its own amount, positive, with the nature apart."""
        move = self._post("2026-02-10", 800.0)
        self._populate()
        parent = self._registers("l10n_br_sped.ecd.i200")
        lines = self._registers("l10n_br_sped.ecd.i250")
        self.assertEqual(len(lines), 2)
        self.assertEqual(parent.res_id, move.id)
        for line in lines:
            self.assertAlmostEqual(line.VL_DC, 800.0, places=2)
        self.assertEqual(set(lines.mapped("IND_DC")), {"D", "C"})

    def test_chart_of_accounts_declares_groups_and_accounts(self):
        """I050 carries both the synthetic groups and the analytic accounts."""
        self._populate()
        registers = self._registers("l10n_br_sped.ecd.i050")
        sintetica = registers.filtered(lambda r: r.COD_CTA == "ECD1")
        analitica = registers.filtered(lambda r: r.COD_CTA == "ECD10")
        self.assertEqual(sintetica.IND_CTA, "S")
        self.assertEqual(analitica.IND_CTA, "A")
        # the analytic account hangs under its group, one level below
        self.assertEqual(analitica.COD_CTA_SUP, "ECD1")
        self.assertEqual(analitica.NIVEL, sintetica.NIVEL + 1)
        # nature comes from the internal group: 01 assets, 04 result
        self.assertEqual(analitica.COD_NAT, "01")
        self.assertEqual(
            registers.filtered(lambda r: r.COD_CTA == "ECD90").COD_NAT, "04"
        )

    def test_trial_balance_has_one_period_per_month(self):
        """I150 covers the escrituracao month by month, with no gap."""
        self._populate()
        registers = self._registers("l10n_br_sped.ecd.i150")
        self.assertEqual(len(registers), 3)
        self.assertEqual(
            [str(r.DT_INI) for r in registers.sorted("DT_INI")],
            ["2026-01-01", "2026-02-01", "2026-03-01"],
        )
        self.assertEqual(str(registers.sorted("DT_INI")[-1].DT_FIN), "2026-03-31")

    def test_trial_balance_carries_opening_movement_and_closing(self):
        """I155 states the opening balance, the movement and the closing one.

        January books 1000 and February another 400. February therefore opens
        at 1000, moves 400 and closes at 1400, which is what makes the trial
        balance tie from one month to the next.
        """
        self._post("2026-01-15", 1000.0)
        self._post("2026-02-15", 400.0)
        self._populate()
        periods = self._registers("l10n_br_sped.ecd.i150").sorted("DT_INI")
        fevereiro = periods[1]
        detail = fevereiro.reg_I155_ids
        caixa = detail.filtered(lambda r: r.COD_CTA == "ECD10")
        self.assertAlmostEqual(caixa.VL_SLD_INI, 1000.0, places=2)
        self.assertEqual(caixa.IND_DC_INI, "D")
        self.assertAlmostEqual(caixa.VL_DEB, 400.0, places=2)
        self.assertAlmostEqual(caixa.VL_CRED, 0.0, places=2)
        self.assertAlmostEqual(caixa.VL_SLD_FIN, 1400.0, places=2)
        self.assertEqual(caixa.IND_DC_FIN, "D")

    def test_credit_balance_is_reported_as_credit_not_as_a_negative(self):
        """A credit balance goes out positive, with the nature saying credit."""
        self._post("2026-01-15", 700.0)
        self._populate()
        periods = self._registers("l10n_br_sped.ecd.i150").sorted("DT_INI")
        detail = periods[0].reg_I155_ids
        vendas = detail.filtered(lambda r: r.COD_CTA == "ECD90")
        self.assertAlmostEqual(vendas.VL_SLD_FIN, 700.0, places=2)
        self.assertEqual(vendas.IND_DC_FIN, "C")
