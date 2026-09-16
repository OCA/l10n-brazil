# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import DereCommon


@tagged("post_install", "-at_install")
class TestDereTables(DereCommon):
    def _event_xml(self, declaration, event_type):
        event = declaration.event_ids.filtered(lambda ev: ev.event_type == event_type)
        self.assertTrue(event.xml_content)
        return etree.fromstring(event.xml_content.encode("utf-8"))

    def test_d1001_benefit_administrator(self):
        declaration = self._create_declaration()
        declaration.action_generate_d1001()
        root = self._event_xml(declaration, "D-1001")
        event = root.find(".//{*}evtInfoContrib")
        self.assertEqual(len(event.get("id") or ""), 42)
        self.assertEqual(root.findtext(".//{*}regTribPrinc"), "2")
        self.assertEqual(root.findtext(".//{*}iniValid"), "2026-10-01")
        self.assertEqual(root.findtext(".//{*}tpAtividade"), "02A")
        self.assertIsNone(root.find(".//{*}servFinanc"))
        self.assertIsNone(root.find(".//{*}prognosticos"))

    def test_d1001_health_operator(self):
        self.company.dere_activity_ids = [Command.set(self.activity_operator.ids)]
        declaration = self._create_declaration("2026-11")
        declaration.action_generate_d1001()
        root = self._event_xml(declaration, "D-1001")
        self.assertEqual(root.findtext(".//{*}tpAtividade"), "05A")

    def test_d1001_requires_health_activity(self):
        self.company.dere_activity_ids = [Command.clear()]
        declaration = self._create_declaration("2026-12")
        with self.assertRaises(UserError):
            declaration.action_generate_d1001()

    def test_d1001_rejects_financial_group_on_health_regime(self):
        financial = self.env.ref("l10n_br_dere.activity_21_01a")
        self.company.dere_activity_ids = [
            Command.set((self.activity_admin | financial).ids)
        ]
        declaration = self._create_declaration("2026-09")
        declaration.action_generate_d1001()
        root = self._event_xml(declaration, "D-1001")
        self.assertIsNone(root.find(".//{*}servFinanc"))
        self.assertEqual(root.findtext(".//{*}tpAtividade"), "02A")

    def test_d1011_exports_parent_and_child(self):
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        root = self._event_xml(declaration, "D-1011")
        self.assertEqual(root.findtext(".//{*}planoCtaRef"), "4")
        self.assertEqual(root.findtext(".//{*}freqEncerr"), "M")
        codes = root.findall(".//{*}cCta")
        self.assertGreaterEqual(len(codes), 2)
        self.assertIn("31000", [node.text for node in codes])
        self.assertIn("311000", [node.text for node in codes])
        splits = {node.text for node in root.findall(".//{*}cDbrMista")}
        self.assertTrue(all(len(code) == 3 for code in splits))
        self.assertEqual(declaration.state, "tables_ok")

    def test_mixed_account_split_must_have_three_digits(self):
        with self.assertRaises(ValidationError):
            self.fee_account.l10n_br_dere_dbr_mista = "00"

    def test_period_mask(self):
        with self.assertRaises(ValidationError):
            self._create_declaration("202610")
