# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

import base64
from datetime import date

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_credito import CreditMixin

OPENING = "l10n_br_pis_cofins.credit.opening"


@tagged("post_install", "-at_install")
class TestCreditOpening(SpedEntradaCommon):
    """The opening balance of the PIS/COFINS credit of a company that comes from
    another system."""

    profit_calculation = "real"

    def _opening(self, **vals):
        values = {
            "company_id": self.company.id,
            "tax_domain": "pis",
            "cutoff_date": date(2026, 7, 1),
            "origin_period": date(2026, 5, 1),
            "cod_cred": "101",
            "amount": 100.0,
            "used_before": 30.0,
        }
        values.update(vals)
        return self.env[OPENING].create(values)

    def test_the_balance_is_the_credit_less_what_was_used(self):
        opening = self._opening()
        self.assertEqual(opening.balance, 70.0)
        opening.used_before = 100.0
        self.assertEqual(opening.balance, 0.0)

    def test_the_used_credit_cannot_be_above_the_credit(self):
        with self.assertRaises(ValidationError):
            self._opening(used_before=120.0)

    def test_the_origin_is_before_the_first_period_of_the_system(self):
        with self.assertRaises(ValidationError):
            self._opening(origin_period=date(2026, 7, 1))

    def test_the_periods_are_the_first_day_of_the_month(self):
        with self.assertRaises(ValidationError):
            self._opening(origin_period=date(2026, 5, 15))

    def test_a_transferred_credit_needs_the_cnpj_of_the_assignor(self):
        with self.assertRaises(ValidationError):
            self._opening(orig_cred="02")
        self._opening(orig_cred="02", cnpj_suc="11222333000181")

    def test_the_accounting_manager_reaches_the_menu_and_the_fiscal_user_only_reads(
        self,
    ):
        menu = self.env.ref("l10n_br_sped_efd_pis_cofins.menu_credit_opening")
        manager = self.env["res.users"].create(
            {
                "name": "Accounting manager",
                "login": "accounting_manager_credit_opening",
                "company_id": self.company.id,
                "company_ids": [(6, 0, self.company.ids)],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("account.group_account_manager").id,
                        ],
                    )
                ],
            }
        )
        visible = (
            self.env["ir.ui.menu"].with_user(manager)._visible_menu_ids(debug=False)
        )
        self.assertIn(menu.id, visible)
        opening = self._opening()
        reader = self.env["res.users"].create(
            {
                "name": "Fiscal user",
                "login": "fiscal_user_credit_opening",
                "company_id": self.company.id,
                "company_ids": [(6, 0, self.company.ids)],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("l10n_br_fiscal.group_user").id,
                        ],
                    )
                ],
            }
        )
        opening.with_user(reader).read(["balance"])
        with self.assertRaises(AccessError):
            opening.with_user(reader).write({"amount": 200.0})


@tagged("post_install", "-at_install")
class TestCreditOpeningChain(CreditMixin, SpedEntradaCommon):
    """The opening balance enters the control as the oldest credit and the
    assessment of the first month of the system starts from it."""

    profit_calculation = "real"

    def _openings(self):
        """PIS: 40.00 of April (10.00 already used) and 20.00 of May, balance
        50.00; COFINS: 200.00 of April (50.00 used) and 100.00 of May, balance
        250.00. The system begins in July."""
        for tax, april, april_used, may in (
            ("pis", 40.0, 10.0, 20.0),
            ("cofins", 200.0, 50.0, 100.0),
        ):
            for month, amount, used in ((4, april, april_used), (5, may, 0.0)):
                self.env[OPENING].create(
                    {
                        "company_id": self.company.id,
                        "tax_domain": tax,
                        "cutoff_date": date(2026, 7, 1),
                        "origin_period": date(2026, month, 1),
                        "cod_cred": "101",
                        "amount": amount,
                        "used_before": used,
                    }
                )

    def _month(self, month, number, sales):
        day = date(2026, month, 10)
        self._entry("fo_compras_compras_comercializacao", number, day)
        for _index in range(sales):
            self._sale(date(2026, month, 12))
        self._assess("pis", month=month)
        self._assess("cofins", month=month)

    def _declaration_month(self, month):
        return self._declaration(
            "efd_pis_cofins", date(2026, month, 1), date(2026, month, 31)
        )

    def test_the_first_assessment_starts_from_the_opening_balance(self):
        self._openings()
        self._month(7, "401", sales=3)
        pis = self.env["l10n_br_tax.assessment"].search(
            [("tax_domain", "=", "pis"), ("date_from", "=", date(2026, 7, 1))]
        )
        self.assertEqual(pis.previous_balance, 50.0)
        # 49.50 of the contribution used 49.50 of the 50.00, 16.50 of own credit
        self.assertAlmostEqual(pis.amount_carried_forward, 17.0, places=2)

    def test_the_opening_balance_is_the_oldest_credit_and_goes_to_the_1100(self):
        self._openings()
        self._month(7, "401", sales=3)
        declaration = self._declaration_month(7)
        rows = {
            rec["PER_APU_CRED"]: rec for rec in self._sped_records(declaration, "1100")
        }
        self.assertEqual(sorted(rows), ["042026", "052026"])
        april, may = rows["042026"], rows["052026"]
        self.assertEqual(april["ORIG_CRED"], "01")
        self.assertEqual(april["COD_CRED"], "101")
        self.assertEqual(april["VL_CRED_APU"], "40,00")
        self.assertEqual(april["VL_CRED_DESC_PA_ANT"], "10,00")
        self.assertEqual(april["SD_CRED_DISP_EFD"], "30,00")
        self.assertEqual(april["VL_CRED_DESC_EFD"], "30,00")
        self.assertEqual(april["SLD_CRED_FIM"], "0")
        self.assertEqual(may["VL_CRED_DESC_EFD"], "19,50")
        self.assertEqual(may["SLD_CRED_FIM"], "0,50")
        m200 = self._sped_records(declaration, "M200")[0]
        self.assertEqual(m200["VL_TOT_CONT_NC_PER"], "49,50")
        self.assertEqual(m200["VL_TOT_CRED_DESC_ANT"], "49,50")
        self.assertEqual(self._number(m200["VL_TOT_CRED_DESC"]), 0.0)
        self.assertEqual(self._number(m200["VL_TOT_CONT_NC_DEV"]), 0.0)
        self.assertEqual(len(self._sped_records(declaration, "1500")), 2)

    def test_the_second_month_goes_on_from_what_is_left(self):
        self._openings()
        self._month(7, "401", sales=3)
        self._month(8, "402", sales=1)
        declaration = self._declaration_month(8)
        rows = {
            rec["PER_APU_CRED"]: rec for rec in self._sped_records(declaration, "1100")
        }
        self.assertEqual(sorted(rows), ["052026", "072026"])
        self.assertEqual(rows["052026"]["SD_CRED_DISP_EFD"], "0,50")
        self.assertEqual(rows["052026"]["VL_CRED_DESC_EFD"], "0,50")
        self.assertEqual(rows["072026"]["VL_CRED_APU"], "16,50")
        self.assertEqual(rows["072026"]["VL_CRED_DESC_EFD"], "16,00")
        self.assertEqual(rows["072026"]["SLD_CRED_FIM"], "0,50")

    def test_the_assessment_warns_when_the_account_is_not_the_opening_balance(self):
        """The system books no entry for the opening balance: when the account of
        the tax to recover does not hold it, the assessment says so (and does not
        block)."""
        self._openings()
        self._month(7, "401", sales=3)
        pis = self.env["l10n_br_tax.assessment"].search(
            [("tax_domain", "=", "pis"), ("date_from", "=", date(2026, 7, 1))]
        )
        self.assertIn("opening balance of the credit", pis.opening_balance_warning)
        account = pis.tax_group_id.with_company(
            self.company
        ).property_tax_receivable_account_id
        other = self.env["account.account"].create(
            {
                "name": "Opening balance",
                "code": "OPENBAL",
                "account_type": "equity",
                "company_id": self.company.id,
            }
        )
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "general")], limit=1
        )
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "date": date(2026, 6, 30),
                "line_ids": [
                    (0, 0, {"account_id": account.id, "debit": 50.0, "credit": 0.0}),
                    (0, 0, {"account_id": other.id, "debit": 0.0, "credit": 50.0}),
                ],
            }
        )
        move.action_post()
        pis.invalidate_recordset()
        self.assertFalse(pis.opening_balance_warning)

    def test_without_an_opening_balance_nothing_changes(self):
        self._month(7, "401", sales=3)
        pis = self.env["l10n_br_tax.assessment"].search(
            [("tax_domain", "=", "pis"), ("date_from", "=", date(2026, 7, 1))]
        )
        self.assertEqual(pis.previous_balance, 0.0)
        self.assertFalse(pis.opening_balance_warning)
        self.assertEqual(self._sped_records(self._declaration_month(7), "1100"), [])

    def test_the_stop_of_the_balance_points_to_the_opening_balance(self):
        """Credit from before the system that is not registered: the message of
        the stop says where to register it."""
        self._openings()
        self._month(7, "401", sales=3)
        self.env[OPENING].search([]).unlink()
        self._set_accountant()
        declaration = self._declaration_month(7)
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("Saldo inicial de crédito de PIS/COFINS", error.exception.args[0])


@tagged("post_install", "-at_install")
class TestCreditOpeningImport(CreditMixin, SpedEntradaCommon):
    """The opening balance read from the last EFD Contribuicoes of the previous
    system (registers 1100 and 1500, and the credit that was left in the own month,
    M100 and M500)."""

    profit_calculation = "real"

    FILE = (
        "|0000|006|0|||01062026|30062026|Empresa|11222333000181|SP|3550308||00|0|\n"
        "|1001|0|\n"
        "|1100|042026|01||101|40,00||40,00|10,00|||30,00|5,00|||||25,00|\n"
        "|1100|052026|01||101|20,00||20,00|0|||20,00|20,00|||||0|\n"
        "|1500|042026|01||101|200,00||200,00|50,00|||150,00|0|||||150,00|\n"
        "|M100|101|0|2000,00|1,65|||33,00|0|0|0|33,00|1||33,00|\n"
        "|M500|101|0|2000,00|7,6|||152,00|0|0|0|152,00|1|52,00|100,00|\n"
        "|1990|3|\n"
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.partner_id.cnpj_cpf = "11.222.333/0001-81"

    def _import(self, text):
        wizard = self.env["l10n_br_pis_cofins.credit.opening.import"].create(
            {
                "company_id": self.company.id,
                "file": base64.b64encode(text.encode("latin-1")),
                "filename": "efd.txt",
            }
        )
        return wizard.action_import()

    def _layers(self, action):
        records = self.env[OPENING].search(action["domain"])
        return {
            (rec.tax_domain, rec.origin_period, rec.cod_cred): rec for rec in records
        }

    def test_the_balance_of_the_1100_and_the_1500_becomes_the_opening_balance(self):
        layers = self._layers(self._import(self.FILE))
        pis_april = layers[("pis", date(2026, 4, 1), "101")]
        self.assertEqual(pis_april.amount, 40.0)
        self.assertEqual(pis_april.balance, 25.0)
        self.assertEqual(pis_april.used_before, 15.0)
        self.assertEqual(pis_april.cutoff_date, date(2026, 7, 1))
        self.assertEqual(layers[("cofins", date(2026, 4, 1), "101")].balance, 150.0)
        self.assertNotIn(("pis", date(2026, 5, 1), "101"), layers, "used up")

    def test_the_credit_left_in_the_own_month_of_the_file_is_carried_too(self):
        """The M100 and the M500 of the month of the file: the balance to use in
        the future periods is what is left in the 1100 and the 1500 and also what
        is left of the credit of the month itself."""
        layers = self._layers(self._import(self.FILE))
        own_pis = layers[("pis", date(2026, 6, 1), "101")]
        self.assertEqual((own_pis.amount, own_pis.used_before), (33.0, 0.0))
        own_cofins = layers[("cofins", date(2026, 6, 1), "101")]
        self.assertEqual((own_cofins.amount, own_cofins.balance), (152.0, 100.0))
        total = sum(rec.balance for key, rec in layers.items() if key[0] == "pis")
        self.assertEqual(total, 58.0)

    def test_the_first_month_pays_the_same_as_the_equivalent_manual_balance(self):
        """The imported layers are the ones a person would have typed, so the first
        month of the system gives the same amount to pay."""
        self._import(self.FILE)
        manual = {
            ("pis", date(2026, 4, 1), 40.0, 15.0),
            ("pis", date(2026, 6, 1), 33.0, 0.0),
        }
        imported = {
            (rec.tax_domain, rec.origin_period, rec.amount, rec.used_before)
            for rec in self.env[OPENING].search([("tax_domain", "=", "pis")])
        }
        self.assertEqual(imported, manual)
        # July: a resale (credit 16.50) and five sales (contribution 82.50): the
        # balance of 58.00 and the credit of the month cover 74.50, 8.00 is due
        self._entry("fo_compras_compras_comercializacao", "401", date(2026, 7, 10))
        for _index in range(5):
            self._sale(date(2026, 7, 12))
        self._assess("pis", month=7)
        self._assess("cofins", month=7)
        self._set_accountant()
        declaration = self._declaration(
            "efd_pis_cofins", date(2026, 7, 1), date(2026, 7, 31)
        )
        m200 = self._sped_records(declaration, "M200")[0]
        self.assertEqual(m200["VL_TOT_CONT_NC_PER"], "82,50")
        self.assertEqual(m200["VL_TOT_CRED_DESC_ANT"], "58,00")
        self.assertEqual(m200["VL_TOT_CRED_DESC"], "16,50")
        self.assertEqual(m200["VL_CONT_NC_REC"], "8,00")

    def test_a_file_of_another_company_is_refused(self):
        other = self.FILE.replace("11222333000181", "99888777000166")
        with self.assertRaises(UserError) as error:
            self._import(other)
        self.assertIn("CNPJ", error.exception.args[0])
        self.assertFalse(self.env[OPENING].search([]))

    def test_a_file_that_is_not_an_efd_contribuicoes_is_refused(self):
        with self.assertRaises(UserError):
            self._import("|9999|1|\n")


@tagged("post_install", "-at_install")
class TestCreditOpeningImportMenu(SpedEntradaCommon):
    """The import of the opening balance is reachable with the list empty."""

    profit_calculation = "real"

    def test_the_import_is_reached_from_the_menu_with_the_list_empty(self):
        """The button of the header of a list only shows with a line selected, and
        the list of the opening balance is empty exactly for who needs the import:
        it has its own menu item, next to the one of the opening balance."""
        menu = self.env.ref("l10n_br_sped_efd_pis_cofins.menu_credit_opening_import")
        action = self.env.ref(
            "l10n_br_sped_efd_pis_cofins.credit_opening_import_action"
        )
        self.assertEqual(menu.action, action)
        self.assertEqual(
            menu.parent_id,
            self.env.ref("l10n_br_sped_efd_pis_cofins.menu_credit_opening").parent_id,
        )
        manager = self.env["res.users"].create(
            {
                "name": "Accounting manager",
                "login": "accounting_manager_credit_import",
                "company_id": self.company.id,
                "company_ids": [(6, 0, self.company.ids)],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("account.group_account_manager").id,
                        ],
                    )
                ],
            }
        )
        visible = (
            self.env["ir.ui.menu"].with_user(manager)._visible_menu_ids(debug=False)
        )
        self.assertIn(menu.id, visible)
