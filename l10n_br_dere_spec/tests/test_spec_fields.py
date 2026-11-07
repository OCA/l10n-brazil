# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDereSpecFields(TransactionCase):
    def test_wave1_models_are_registered(self):
        for name in (
            "dere.12.evtinfocontrib",
            "dere.12.evtpgcc",
            "dere.12.infoconta",
            "dere.12.evtbalancete",
            "dere.12.balanceteconta",
            "dere.12.evtaplicrestec",
            "dere.12.detativo",
            "dere.12.evtreldeducoes",
            "dere.12.infodeducao",
            "dere.12.itemdfe",
            "dere.12.evtreabertmensal",
            "dere.12.evtfechmensal",
            "dere.12.infobcn",
            "dere.12.evtretornostabela",
            "dere.12.detevento",
            "dere.12.detlacuna",
            "dere.12.gtotalcodtrib",
            "dere.12.detbc",
            "dere.12.totaltributos",
        ):
            self.assertIn(name, self.env.registry)

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

    def test_event_id_size_matches_xsd(self):
        field = self.env["dere.12.evtinfocontrib"]._fields["dere12_id"]
        self.assertEqual(field.size, 42)

    def test_mixed_account_split_is_three_digits(self):
        field = self.env["dere.12.infoconta"]._fields["dere12_cDbrMista"]
        self.assertEqual(field.size, 3)

    def test_main_regime_values(self):
        field = self.env["dere.12.evtinfocontrib"]._fields["dere12_regTribPrinc"]
        self.assertEqual(
            {key for key, _label in field.selection},
            {"1", "2", "3", "9"},
        )

    def test_deduction_operation_includes_rectification(self):
        field = self.env["dere.12.evtreldeducoes"]._fields["dere12_tpOper"]
        self.assertEqual(
            {key for key, _label in field.selection},
            {"1", "2", "3", "4"},
        )

    def test_reserve_asset_id_size(self):
        field = self.env["dere.12.detativo"]._fields["dere12_idAtivo"]
        self.assertEqual(field.size, 30)
