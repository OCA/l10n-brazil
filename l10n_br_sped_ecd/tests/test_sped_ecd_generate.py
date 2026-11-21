# Copyright 2024 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
"""Generation of block I from the Odoo ledger: the tests assert amounts."""
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
        """Pull from I010, as `button_populate_sped_from_odoo` does."""
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
        """The entry carries its accounting date and the total of its debits."""
        self._post("2026-02-10", 1500.0)
        self._populate()
        registers = self._registers("l10n_br_sped.ecd.i200")
        self.assertEqual(len(registers), 1)
        self.assertEqual(str(registers.DT_LCTO), "2026-02-10")
        self.assertAlmostEqual(registers.VL_LCTO, 1500.0, places=2)

    def test_entries_on_the_period_edges_are_included(self):
        """The period bounds are inclusive."""
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

    def test_trial_balance_periods_stay_inside_a_partial_escrituracao(self):
        """A bookkeeping that starts and ends mid-month does not overflow it."""
        self.declaration.write({"DT_INI": "2026-01-15", "DT_FIN": "2026-03-10"})
        self._populate()
        periods = self._registers("l10n_br_sped.ecd.i150").sorted("DT_INI")
        self.assertEqual(str(periods[0].DT_INI), "2026-01-15")
        self.assertEqual(str(periods[-1].DT_FIN), "2026-03-10")

    def test_trial_balance_carries_opening_movement_and_closing(self):
        """February opens at the 1000 of January, moves 400 and closes at 1400."""
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

    def test_file_records_follow_the_layout(self):
        """What the PVA refuses: functional currency fields in a bookkeeping
        without one, a mandatory zero left blank, the SCP and replaced hash
        filled with a zero, an untimely date in an ordinary entry, an item
        without history and a missing 0007."""
        self._post("2026-02-10", 1500.0)
        self.declaration.button_populate_sped_from_odoo()
        lines = self.declaration._generate_sped_text().split("\n")

        def fields_of(code):
            return [line.split("|")[1:-1] for line in lines if line[1:5] == code]

        # without IDENT_MF = S the I155 has 9 fields, the I200 6, the I250 9,
        # the REG included
        caixa = next(f for f in fields_of("I155") if f[1] == "ECD10")
        self.assertEqual(len(caixa), 9)
        self.assertEqual(caixa[3:8], ["0", "D", "1500,00", "0", "1500,00"])
        self.assertEqual({len(f) for f in fields_of("I200")}, {6})
        self.assertEqual({len(f) for f in fields_of("I250")}, {9})
        # no untimely entry, so no DT_LCTO_EXT; every item carries a history
        self.assertEqual({f[5] for f in fields_of("I200")}, {""})
        self.assertTrue(all(f[7] for f in fields_of("I250")))
        self.assertEqual(fields_of("I010")[0][2], "9.00")
        # the 0007 is mandatory: 00 when there is no other registration
        self.assertEqual(fields_of("0007"), [["0007", "00", ""]])
        header = fields_of("0000")[0]
        # TIP_ECD (17) is mandatory, COD_HASH_SUB (15) and COD_SCP (18) are not
        self.assertEqual(header[16], "0")
        self.assertEqual(header[14], "")
        self.assertEqual(header[17], "")

    def test_result_accounts_open_the_fiscal_year_at_zero(self):
        """Last year's revenue does not carry over, the cash balance does."""
        self._post("2025-12-20", 500.0)
        self._post("2026-01-15", 300.0)
        self._populate()
        periods = self._registers("l10n_br_sped.ecd.i150").sorted("DT_INI")
        detail = periods[0].reg_I155_ids
        caixa = detail.filtered(lambda r: r.COD_CTA == "ECD10")
        vendas = detail.filtered(lambda r: r.COD_CTA == "ECD90")
        self.assertAlmostEqual(caixa.VL_SLD_INI, 500.0, places=2)
        self.assertAlmostEqual(caixa.VL_SLD_FIN, 800.0, places=2)
        self.assertAlmostEqual(vendas.VL_SLD_INI, 0.0, places=2)
        self.assertAlmostEqual(vendas.VL_SLD_FIN, 300.0, places=2)
