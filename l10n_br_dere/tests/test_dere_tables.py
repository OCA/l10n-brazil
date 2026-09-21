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
        event = self._event(declaration, event_type)
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
        parent = declaration.pgcc_account_ids.filtered(
            lambda rec: rec.group_id == self.parent_group
        )
        child = declaration.pgcc_account_ids.filtered(
            lambda rec: rec.account_id == self.fee_account
        )
        self.assertEqual(parent.dere12_indCta, "S")
        self.assertFalse(parent.account_id)
        self.assertEqual(child.dere12_indCta, "A")
        self.assertEqual(child.dere12_cCtaSup, parent.dere12_cCta)
        self.assertEqual(self.fee_account.group_id, self.parent_group)
        self.assertEqual(self.fee_account.l10n_br_dere_ind_cta, "A")
        self.assertEqual(self.fee_account.l10n_br_dere_nivel_cta, 2)
        splits = {node.text for node in root.findall(".//{*}cDbrMista")}
        self.assertTrue(all(len(code) == 3 for code in splits))
        self.assertEqual(declaration.state, "draft")
        self.assertTrue(declaration.can_generate_tables)
        self.assertTrue(declaration.can_send_tables)
        self.assertFalse(declaration.can_generate_trial)
        self.assertFalse(declaration.primary_action)

    def test_d1011_inherits_group_mapping_on_analytic_account(self):
        inherited = self.env["account.account"].create(
            {
                "name": "Inherited health revenue",
                "code": "DERE312",
                "account_type": "income",
                "company_ids": [Command.set(self.company.ids)],
                "l10n_br_dere_cta_interna": "312",
                "l10n_br_dere_cod_trib": self.tax_admin_fee.id,
            }
        )
        self.assertEqual(inherited.group_id, self.parent_group)
        self.assertEqual(inherited._dere_cta_ref(), "12011")
        self.assertEqual(inherited._dere_nat_cta(), "C")
        self.assertEqual(inherited._dere_cod_nat(), "4")
        declaration = self._create_declaration("2026-01")
        declaration.action_generate_d1011()
        line = declaration.pgcc_account_ids.filtered(
            lambda rec: rec.account_id == inherited
        )
        self.assertEqual(line.dere12_cCtaRef, "12011")
        self.assertEqual(line.dere12_natCta, "C")
        self.assertEqual(line.dere12_codNat, "4")
        self.assertEqual(line.dere12_cCtaSup, "31000")
        self.assertEqual(line.dere12_indCta, "A")

    def test_d1011_emits_ancestor_groups_without_cta_ref(self):
        self.parent_group.l10n_br_dere_cta_ref = False
        self.parent_group.l10n_br_dere_nat_cta = False
        self.parent_group.l10n_br_dere_cod_nat = False
        declaration = self._create_declaration("2026-02")
        declaration.action_generate_d1011()
        parent = declaration.pgcc_account_ids.filtered(
            lambda rec: rec.group_id == self.parent_group
        )
        self.assertTrue(parent)
        self.assertEqual(parent.dere12_cCta, "31000")
        self.assertEqual(parent.dere12_cCtaRef, "31")
        self.assertEqual(parent.dere12_indCta, "S")
        self.assertEqual(parent.dere12_natCta, "C")
        self.assertEqual(parent.dere12_codNat, "4")
        child = declaration.pgcc_account_ids.filtered(
            lambda rec: rec.account_id == self.fee_account
        )
        self.assertEqual(child.dere12_cCtaSup, parent.dere12_cCta)

    def test_d1011_uses_company_language_account_name(self):
        self.env["res.lang"]._activate_lang("pt_BR")
        self.company.partner_id.lang = "pt_BR"
        self.fee_account.update_field_translations(
            "name", {"pt_BR": "Administration fees PT"}
        )
        declaration = self._create_declaration("2026-08")
        declaration.action_generate_tables()
        fee_pgcc = declaration.pgcc_account_ids.filtered(
            lambda rec: rec.account_id == self.fee_account
        )
        self.assertEqual(fee_pgcc.dere12_nomeCta, "Administration fees PT")
        root = self._event_xml(declaration, "D-1011")
        names = [node.text for node in root.findall(".//{*}nomeCta")]
        self.assertIn("Administration fees PT", names)
        self.assertEqual(
            fee_pgcc.with_context(lang="en_US").account_name,
            "Administration fees",
        )
        self.assertEqual(
            fee_pgcc.with_context(lang="pt_BR").account_name,
            "Administration fees PT",
        )

    def test_mixed_account_split_must_have_three_digits(self):
        with self.assertRaises(ValidationError):
            self.fee_account.l10n_br_dere_dbr_mista = "00"

    def test_period_mask(self):
        with self.assertRaises(ValidationError):
            self._create_declaration("202610")

    def test_declaration_form_exposes_spec_fields(self):
        views = self.env["l10n_br_dere.declaration"].get_views([(False, "form")])
        pgcc_fields = views["models"]["l10n_br_dere.pgcc.account"]["fields"]
        trial_fields = views["models"]["l10n_br_dere.trial.line"]["fields"]
        self.assertIn("dere12_cCta", pgcc_fields)
        self.assertIn("dere12_nomeCta", pgcc_fields)
        self.assertIn("account_name", pgcc_fields)
        self.assertIn("dere12_nivelCta", pgcc_fields)
        self.assertIn("dere12_cCtaSup", pgcc_fields)
        self.assertIn("dere12_cCta", trial_fields)
        self.assertIn("account_name", trial_fields)
        self.assertIn("dere12_vApur", trial_fields)
        self.assertIn('name="dere12_cCta"', views["views"]["form"]["arch"])
        self.assertIn('name="account_name"', views["views"]["form"]["arch"])
        self.assertIn('name="dere12_nivelCta"', views["views"]["form"]["arch"])
        self.assertIn('optional="hide"', views["views"]["form"]["arch"])
        self.assertIn("state != 'draft'", views["views"]["form"]["arch"])
        self.assertIn("state == 'closed'", views["views"]["form"]["arch"])
