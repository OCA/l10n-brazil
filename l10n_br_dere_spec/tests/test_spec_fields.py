# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDereSpecFields(TransactionCase):
    def test_wave1_models_are_registered(self):
        for name in (
            "dere.12.d1001.evtinfocontrib",
            "dere.12.d1001.infocontrib",
            "dere.12.d1011.evtpgcc",
            "dere.12.d1011.infoconta",
            "dere.12.d1101.evtbalancete",
            "dere.12.d1101.infoconta",
            "dere.12.d1106.evtaplicrestec",
            "dere.12.d1106.detativo",
            "dere.12.d1121.evtreldeducoes",
            "dere.12.d1121.infodeducao",
            "dere.12.d1121.itemdfe",
            "dere.12.d1198.evtreabertmensal",
            "dere.12.d1199.evtfechmensal",
            "dere.12.d1199.infobcn",
            "dere.12.d9001.evtretornotabela",
            "dere.12.d9001.detevento",
            "dere.12.d9001.detlacuna",
            "dere.12.d9101.gtotalcodtrib",
            "dere.12.detbc",
            "dere.12.totaltributos",
        ):
            self.assertIn(name, self.env.registry)

    def test_chart_and_trial_accounts_do_not_share_a_model(self):
        chart = self.env["dere.12.d1011.infoconta"]._fields
        trial = self.env["dere.12.d1101.infoconta"]._fields
        self.assertIn("dere12_cCtaInterna", chart)
        self.assertNotIn("dere12_cCtaInterna", trial)
        self.assertIn("dere12_vApur", trial)
        self.assertNotIn("dere12_vApur", chart)

    def test_return_suffixes_repeated_xsd_names(self):
        fields_map = self.env["dere.12.detbc"]._fields
        for name in (
            "dere12_vDedBCNIBS",
            "dere12_vDedBCNCBS",
            "dere12_vSaldoFinalBCNIBS",
            "dere12_vSaldoFinalBCNCBS",
        ):
            self.assertIn(name, fields_map)
        self.assertEqual(fields_map["dere12_pIBS"].get_digits(self.env), (9, 6))

    def test_main_regime_values(self):
        field = self.env["dere.12.d1001.infocontrib"]._fields["dere12_regTribPrinc"]
        self.assertEqual(
            {key for key, _label in field.selection},
            {"1", "2", "3", "9"},
        )

    def test_deduction_operation_includes_rectification(self):
        field = self.env["dere.12.d1121.ideevento"]._fields["dere12_tpOper"]
        self.assertEqual(
            {key for key, _label in field.selection},
            {"1", "2", "3", "4"},
        )

    def test_reserve_asset_id_is_a_char(self):
        field = self.env["dere.12.d1106.detativo"]._fields["dere12_idAtivo"]
        self.assertEqual(field.type, "char")
