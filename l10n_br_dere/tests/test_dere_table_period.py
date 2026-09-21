# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_dere.constants import STRUCTURED_EVENT_ID_RE
from odoo.addons.l10n_br_dere.models.xml_builder import _money

from .common import DereCommon


@tagged("post_install", "-at_install")
class TestDereTablePeriod(DereCommon):
    def test_declaration_links_covering_table_period(self):
        period = self.env["l10n_br_dere.table.period"].create(
            {
                "company_id": self.company.id,
                "ini_valid": "2028-01-01",
            }
        )
        declaration = self.env["l10n_br_dere.declaration"].create(
            {"company_id": self.company.id, "per_apur": "2028-10"}
        )
        self.assertEqual(declaration.table_period_id, period)
        self.assertEqual(declaration.ini_valid, period.ini_valid)

    def test_generate_tables_creates_period_events(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        period = declaration.table_period_id
        self.assertTrue(period)
        self.assertEqual(period.state, "generated")
        self.assertEqual(len(period.event_ids), 2)
        self.assertFalse(
            declaration.event_ids.filtered(
                lambda ev: ev.event_type in ("D-1001", "D-1011")
            )
        )
        event = self._event(declaration, "D-1001")
        self.assertRegex(event.event_id_attr, STRUCTURED_EVENT_ID_RE)
        self.assertTrue(event.event_id_attr.startswith("DeRE10011"))
        self.assertIn(
            self.company._dere_cnpj_root().rjust(14, "0"), event.event_id_attr
        )

    def test_event_ids_are_sequential_in_the_same_second(self):
        Event = self.env["l10n_br_dere.event"]
        Event._event_id_seq.clear()
        first = Event._generate_event_id(event_type="D-1001", company=self.company)
        second = Event._generate_event_id(event_type="D-1011", company=self.company)
        self.assertEqual(first[-5:], "00001")
        if first[23:37] == second[23:37]:
            self.assertEqual(second[-5:], "00002")

    def test_d1011_requires_tax_code_on_analytic_accounts(self):
        self.equity_account.l10n_br_dere_cod_trib = False
        declaration = self._create_declaration("2026-05")
        with self.assertRaises(UserError) as error:
            declaration.action_generate_d1011()
        self.assertIn("taxation code", str(error.exception))

    def test_nbr5891_rounds_half_to_even(self):
        self.assertEqual(_money(1.225), "1.22")
        self.assertEqual(_money(1.235), "1.24")
        self.assertEqual(_money(-0.001), "0.00")

    def test_accepting_tables_unlocks_trial_generation(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self.assertFalse(declaration.can_generate_trial)
        self._accept_tables(declaration)
        self.assertTrue(declaration.can_generate_trial)
        self.assertTrue(declaration.table_period_id.tables_accepted())

    def test_d1199_blocks_when_pgcc_receipt_changed(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._accept_tables(declaration)
        self._post_entry("2026-10-10", self.receivable, self.fee_account, 10.0)
        declaration.action_generate_d1101()
        self._event(declaration, "D-1101").nr_recibo_prev = "old-receipt"
        self._event(declaration, "D-1011").with_context(
            dere_force_event_write=True
        ).nr_recibo = "new-receipt"
        with self.assertRaises(UserError):
            declaration.action_generate_d1199()
