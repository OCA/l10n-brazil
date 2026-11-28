# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase


class TestResultClosingWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "Closing Company"})
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[cls.company.id])
        )
        account = cls.env["account.account"]

        def conta(code, account_type):
            return account.create(
                {
                    "code": code,
                    "name": code,
                    "account_type": account_type,
                    "company_ids": [(6, 0, cls.company.ids)],
                }
            )

        cls.cash = conta("1.01", "asset_current")
        cls.revenue = conta("3.01", "income")
        cls.other_revenue = conta("3.02", "income_other")
        cls.cost = conta("4.01", "expense_direct_cost")
        cls.equity = conta("2.03", "equity")
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "General",
                "code": "GEN",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls._entry(date(2026, 1, 10), cls.revenue, 1000.0)
        cls._entry(date(2026, 2, 10), cls.other_revenue, 50.0)
        cls._entry(date(2026, 3, 10), cls.cost, -300.0)
        # fora do periodo
        cls._entry(date(2026, 4, 10), cls.revenue, 70.0)

    @classmethod
    def _entry(cls, day, account, amount):
        move = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": day,
                "journal_id": cls.journal.id,
                "line_ids": [
                    (0, 0, {"account_id": cls.cash.id, "balance": amount}),
                    (0, 0, {"account_id": account.id, "balance": -amount}),
                ],
            }
        )
        move.action_post()
        return move

    def _close(self, date_from=date(2026, 1, 1), date_to=date(2026, 3, 31)):
        form = Form(self.env["l10n_br_account.result.closing.wizard"])
        form.date_from = date_from
        form.date_to = date_to
        if not form.equity_account_id:
            form.equity_account_id = self.equity
        action = form.save().action_close()
        return self.env["account.move"].browse(action["res_id"])

    def _balance(self, account, date_to=date(2026, 3, 31)):
        lines = self.env["account.move.line"].search(
            [
                ("account_id", "=", account.id),
                ("parent_state", "=", "posted"),
                ("date", "<=", date_to),
            ]
        )
        return sum(lines.mapped("balance"))

    def test_closing_brings_the_result_to_equity(self):
        move = self._close()
        self.assertTrue(move.l10n_br_sped_result_closing)
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.date, date(2026, 3, 31))
        self.assertEqual(move.journal_id, self.journal)
        for account in (self.revenue, self.other_revenue, self.cost):
            self.assertAlmostEqual(self._balance(account), 0.0)
        # lucro do trimestre: 1000 + 50 - 300, a credito do PL
        self.assertAlmostEqual(self._balance(self.equity), -750.0)
        self.assertEqual(len(move.line_ids), 4)
        # o abril fica de fora
        self.assertAlmostEqual(self._balance(self.revenue, date(2026, 4, 30)), -70.0)

    def test_next_period_suggests_the_equity_account(self):
        self._close()
        form = Form(self.env["l10n_br_account.result.closing.wizard"])
        self.assertEqual(form.equity_account_id, self.equity)
        self.assertEqual(form.journal_id, self.journal)
        move = self._close(date(2026, 4, 1), date(2026, 6, 30))
        # so o abril: o encerramento de marco nao entra no saldo
        self.assertAlmostEqual(
            sum(
                move.line_ids.filtered(
                    lambda line: line.account_id == self.equity
                ).mapped("balance")
            ),
            -70.0,
        )

    def test_period_already_closed(self):
        self._close()
        with self.assertRaisesRegex(UserError, "already closed"):
            self._close(date(2026, 3, 1), date(2026, 3, 31))

    def test_period_without_result(self):
        with self.assertRaisesRegex(UserError, "no result"):
            self._close(date(2026, 7, 1), date(2026, 9, 30))

    def test_accounting_manager_closes(self):
        manager = self.env["res.users"].create(
            {
                "name": "Accounting Manager",
                "login": "closing_manager",
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [
                    (6, 0, [self.env.ref("account.group_account_manager").id])
                ],
            }
        )
        wizard = (
            self.env["l10n_br_account.result.closing.wizard"]
            .with_user(manager)
            .create(
                {
                    "date_from": date(2026, 1, 1),
                    "date_to": date(2026, 3, 31),
                    "equity_account_id": self.equity.id,
                }
            )
        )
        move = self.env["account.move"].browse(wizard.action_close()["res_id"])
        self.assertTrue(move.l10n_br_sped_result_closing)
        self.assertEqual(move.create_uid, manager)
