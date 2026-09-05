# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from nfelib.nfse.bindings.v1_0.dps_v1_00 import Dps

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNfseSchema(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def _assert_valid(self, xml_id):
        document = self.env.ref(xml_id, raise_if_not_found=False)
        if not document:
            self.skipTest("l10n_br_nfse_nacional demo data is not installed")
        xml = document._serialize([])[0].to_xml()
        self.assertEqual(Dps.schema_validation(xml), [])

    def test_dps_simples_nacional_validates(self):
        self._assert_valid("l10n_br_nfse_nacional.demo_nfse_sn")

    def test_dps_regime_normal_validates(self):
        self._assert_valid("l10n_br_nfse_nacional.demo_nfse_lc")
