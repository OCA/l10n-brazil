# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree
from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.tests.common import TransactionCase, tagged

from .common import set_provedor_nacional

NS = {"n": "http://www.sped.fazenda.gov.br/nfse"}


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
        set_provedor_nacional(document)
        xml = document._serialize([])[0].to_xml()
        self.assertEqual(Dps.schema_validation(xml), [])

    def test_dps_simples_nacional_validates(self):
        self._assert_valid("l10n_br_nfse_nacional.demo_nfse_sn")

    def test_dps_regime_normal_validates(self):
        self._assert_valid("l10n_br_nfse_nacional.demo_nfse_lc")

    def test_dps_declares_suspension_and_municipal_benefit(self):
        document = self.env.ref("l10n_br_nfse_nacional.demo_nfse_lc", False)
        if not document:
            self.skipTest("l10n_br_nfse_nacional demo data is not installed")
        set_provedor_nacional(document)
        document.company_id.nfse_suspension_process = "1" * 30
        line = document.fiscal_line_ids[0]
        line.city_taxation_code_id = self.env[
            "l10n_br_fiscal.city.taxation.code"
        ].create(
            {
                "code": "001",
                "name": "Benefit test",
                "nfse_benefit_code": "42024040400001",
                "nfse_benefit_type": "2",
            }
        )
        line.write({"issqn_reduction": 40.0, "issqn_eligibility": "6"})
        xml = document._serialize([])[0].to_xml()
        self.assertEqual(Dps.schema_validation(xml), [])
        trib_mun = etree.fromstring(xml.encode()).xpath("//n:tribMun", namespaces=NS)[0]
        values = {
            path: trib_mun.findtext(path, namespaces=NS)
            for path in ("n:exigSusp/n:tpSusp", "n:BM/n:nBM", "n:BM/n:pRedBCBM")
        }
        self.assertEqual(
            values,
            {
                "n:exigSusp/n:tpSusp": "1",
                "n:BM/n:nBM": "42024040400001",
                "n:BM/n:pRedBCBM": "40.00",
            },
        )
