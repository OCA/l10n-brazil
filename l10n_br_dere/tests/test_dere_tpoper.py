# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_dere.models import xml_builder

from .common import DereCommon


@tagged("post_install", "-at_install")
class TestDereTpOper(DereCommon):
    def test_xml_builder_table_nova_validade_and_exclusion(self):
        header = {
            "id": "A" + "0" * 41,
            "tpOper": "2",
            "tpAmb": "2",
            "verAplic": "test",
            "nrInsc": "12345678",
            "iniValid": "2026-01-01",
            "novaValidade": {"iniValid": "2026-02-01", "fimValid": "2026-12-31"},
            "regTribPrinc": "2",
            "tpAtividadeSaude": ["02A"],
            "planoCtaRef": "2",
            "freqEncerr": "M",
        }
        d1001 = xml_builder.build_d1001(header)
        self.assertIn("<tpOper>2</tpOper>", d1001)
        self.assertIn("<novaValidade>", d1001)
        self.assertIn("<iniValid>2026-02-01</iniValid>", d1001)
        exclude = xml_builder.build_d1001({**header, "tpOper": "3", "motExcl": "2"})
        self.assertIn("<motExcl>2</motExcl>", exclude)
        self.assertNotIn("<infoContrib>", exclude)
        d1011 = xml_builder.build_d1011({**header, "tpOper": "3", "motExcl": "9"}, [])
        self.assertNotIn("<infoPGCC>", d1011)

    def test_xml_builder_periodic_replace_exclude_and_d1121_rectify(self):
        header = {
            "id": "A" + "0" * 41,
            "tpOper": "2",
            "tpAmb": "2",
            "verAplic": "test",
            "nrInsc": "12345678",
            "perApur": "2026-01",
            "nrRecibo": "1101-202601-" + "0" * 19,
        }
        d1101 = xml_builder.build_d1101(
            header,
            [
                {
                    "cCta": "311",
                    "natSaldoInic": "C",
                    "vSaldoInic": 0,
                    "vMovDebt": 0,
                    "vMovCred": 10,
                    "natSaldoFinal": "C",
                    "vSaldoFinal": 10,
                    "vApur": 10,
                    "natVApur": "C",
                }
            ],
        )
        self.assertIn("<nrRecibo>1101-202601-", d1101)
        exclude = xml_builder.build_d1101({**header, "tpOper": "3", "motExcl": "2"}, [])
        self.assertNotIn("<infoBalancete>", exclude)
        reserve = xml_builder.build_d1106(
            {
                **header,
                "tpOper": "3",
                "motExcl": "3",
                "nrRecibo": "1106-202601-" + "0" * 19,
            },
            [],
        )
        self.assertNotIn("<infoAplicResTec>", reserve)
        key = self._nfe_access_key(8, "2026-01")
        rectify = xml_builder.build_d1121(
            {
                **header,
                "tpOper": "4",
                "finEvt": "2",
            },
            [
                {
                    "chDFeRetif": key,
                    "dtEmi": "2026-01-15",
                    "tpAtiv": "06",
                    "vOper": 100,
                    "vDed": 80,
                }
            ],
        )
        self.assertIn("<finEvt>2</finEvt>", rectify)
        self.assertIn(f"<chDFeRetif>{key}</chDFeRetif>", rectify)
        self.assertNotIn("<nrRecibo>", rectify)
        self.assertNotIn("<chDFe>", rectify)

    def test_cannot_include_active_trial_or_operate_when_closed(self):
        declaration = self._create_declaration("2027-05")
        declaration.action_generate_tables()
        self._accept_tables(declaration)
        self._post_entry("2027-05-10", self.receivable, self.fee_account, 20.0)
        declaration.action_generate_d1101()
        event = self._event(declaration, "D-1101")
        event.write(
            {
                "state": "accepted",
                "nr_recibo": self._event_receipt("D-1101", "2027-05"),
                "cd_retorno": "1",
            }
        )
        declaration.invalidate_recordset()
        self.assertFalse(declaration.can_generate_trial)
        self.assertTrue(declaration.can_replace_trial)
        with self.assertRaises(UserError):
            declaration._generate_d1101(tp_oper="1")
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        self.assertEqual(declaration.state, "closed")
        with self.assertRaises(UserError):
            declaration._generate_d1101(tp_oper="2")
        with self.assertRaises(UserError):
            declaration._generate_d1101(tp_oper="3", extra={"motExcl": "2"})

    def test_exclude_trial_then_include_again(self):
        declaration = self._create_declaration("2027-06")
        declaration.action_generate_tables()
        self._accept_tables(declaration)
        self._post_entry("2027-06-10", self.receivable, self.fee_account, 15.0)
        declaration.action_generate_d1101()
        self._event(declaration, "D-1101").write(
            {
                "state": "accepted",
                "nr_recibo": self._event_receipt("D-1101", "2027-06"),
                "cd_retorno": "1",
            }
        )
        declaration._generate_d1101(tp_oper="3", extra={"motExcl": "2"})
        exclusion = self._event(declaration, "D-1101")
        self.assertEqual(exclusion.tp_oper, "3")
        self.assertNotIn("<infoBalancete>", exclusion.xml_content)
        exclusion.write(
            {
                "state": "accepted",
                "nr_recibo": "1101-202706-" + "1" * 19,
                "cd_retorno": "1",
            }
        )
        declaration.invalidate_recordset()
        self.assertFalse(declaration._active_event("D-1101"))
        self.assertTrue(declaration.can_generate_trial)
        declaration.action_generate_d1101()
        included = self._event(declaration, "D-1101")
        self.assertEqual(included.tp_oper, "1")
        self.assertIn("<infoBalancete>", included.xml_content)

    def test_table_replace_emits_nova_validade(self):
        declaration = self._create_declaration("2027-08")
        period = self._table_period(declaration)
        period.action_generate_tables()
        self._accept_tables(declaration)
        original_ini = period.ini_valid
        period._generate_table_operation(
            tp_oper="2",
            extra={
                "novaValidade": {
                    "iniValid": "2027-02-01",
                    "fimValid": "2027-12-31",
                }
            },
        )
        replacement = self._event(declaration, "D-1001")
        self.assertEqual(replacement.tp_oper, "2")
        self.assertIn("<novaValidade>", replacement.xml_content)
        self.assertIn("<iniValid>2027-02-01</iniValid>", replacement.xml_content)
        self.assertEqual(period.ini_valid, original_ini)
        period.apply_return(
            replacement,
            "1",
            nr_recibo=self._event_receipt("D-1001", "2027-08"),
        )
        self.assertEqual(str(period.ini_valid), "2027-02-01")
        self.assertEqual(str(period.fim_valid), "2027-12-31")
        period._generate_table_operation(tp_oper="3", extra={"motExcl": "2"})
        exclusion = self._event(declaration, "D-1001")
        self.assertEqual(exclusion.tp_oper, "3")
        self.assertNotIn("<infoContrib>", exclusion.xml_content)
        self.assertNotIn("<infoPGCC>", self._event(declaration, "D-1011").xml_content)

    def test_d1121_rectify_only_after_reopening(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial("2027-07")
        with self.assertRaises(UserError):
            declaration._generate_d1121(tp_oper="4", extra={"finEvt": "1"})
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        self._accept_reopening(declaration)
        self.assertTrue(declaration._can_rectify_d1121())
        self.assertFalse(declaration.can_generate_d1121)

    def test_wizard_rejects_identical_nova_validade(self):
        declaration = self._create_declaration("2027-09")
        period = self._table_period(declaration)
        period.action_generate_tables()
        self._accept_tables(declaration)
        wizard = self.env["l10n_br_dere.event.operation.wizard"].create(
            {
                "table_period_id": period.id,
                "event_type": "D-1011",
                "tp_oper": "2",
                "change_validity": True,
                "nova_ini_valid": period.ini_valid,
                "nova_fim_valid": period.fim_valid,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_wizard_d1121_rectify_requires_finevt_and_lines(self):
        self.company.dere_subject_d1121 = True
        declaration = self._prepare_trial("2027-10")
        first = self.env["l10n_br_dere.deduction.line"].create(
            {
                "declaration_id": declaration.id,
                "dere12_tpDFe": "03",
                "dere12_chDFe": self._nfe_access_key(1, "2027-10"),
                "dere12_dtEmi": "2027-10-01",
                "dere12_tpAtiv": "06",
                "dere12_vOper": 50.0,
                "dere12_vDedTotal": 50.0,
                "dere12_vDed": 50.0,
            }
        )
        second = self.env["l10n_br_dere.deduction.line"].create(
            {
                "declaration_id": declaration.id,
                "dere12_tpDFe": "03",
                "dere12_chDFe": self._nfe_access_key(2, "2027-10"),
                "dere12_dtEmi": "2027-10-02",
                "dere12_tpAtiv": "06",
                "dere12_vOper": 30.0,
                "dere12_vDedTotal": 30.0,
                "dere12_vDed": 30.0,
            }
        )
        declaration.action_generate_d1121()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        self._accept_reopening(declaration)
        wizard = self.env["l10n_br_dere.event.operation.wizard"].create(
            {
                "declaration_id": declaration.id,
                "event_type": "D-1121",
                "tp_oper": "4",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.fin_evt = "1"
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.deduction_line_ids = first
        wizard.action_confirm()
        event = self._event(declaration, "D-1121")
        self.assertEqual(event.tp_oper, "4")
        self.assertIn("<finEvt>1</finEvt>", event.xml_content)
        self.assertIn(first.dere12_chDFe, event.xml_content)
        self.assertNotIn(second.dere12_chDFe, event.xml_content)

    def test_replace_d1011_leaves_accepted_d1001(self):
        declaration = self._create_declaration("2027-11")
        period = self._table_period(declaration)
        period.action_generate_tables()
        self._accept_tables(declaration)
        d1001 = self._event(declaration, "D-1001")
        d1011 = self._event(declaration, "D-1011")
        self.assertTrue(d1001.can_replace_event)
        self.assertTrue(d1011.can_replace_event)
        action = d1011.action_replace_event()
        wizard = self.env["l10n_br_dere.event.operation.wizard"].browse(
            action["res_id"]
        )
        self.assertEqual(wizard.event_type, "D-1011")
        wizard.action_confirm()
        replacement = self._event(declaration, "D-1011")
        self.assertEqual(replacement.tp_oper, "2")
        self.assertEqual(self._event(declaration, "D-1001").id, d1001.id)
        self.assertEqual(self._event(declaration, "D-1001").tp_oper, "1")
        self._accept_event(declaration, "D-1011")
        d1011.invalidate_recordset(["can_replace_event", "can_exclude_event"])
        replacement.invalidate_recordset(["can_replace_event", "can_exclude_event"])
        self.assertFalse(d1011.can_replace_event)
        self.assertTrue(self._event(declaration, "D-1011").can_replace_event)

    def test_replace_accepted_d1101_from_event_row(self):
        declaration = self._prepare_trial("2027-12")
        self._accept_event(declaration, "D-1101")
        event = self._event(declaration, "D-1101")
        self.assertTrue(event.can_replace_event)
        self.assertTrue(event.can_exclude_event)
        event.action_replace_event()
        replacement = self._event(declaration, "D-1101")
        self.assertEqual(replacement.tp_oper, "2")
        self.assertIn("<tpOper>2</tpOper>", replacement.xml_content)
