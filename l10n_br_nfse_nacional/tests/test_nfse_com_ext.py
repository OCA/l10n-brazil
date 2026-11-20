# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.tests import TransactionCase, tagged

from .common import set_provedor_nacional


@tagged("post_install", "-at_install")
class TestNfseComExt(TransactionCase):
    """An exported service carries the comExt group (rule E0330): it is asked
    for when tribISSQN is 3 (export of service) or the taker is abroad."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls.env.ref("l10n_br_nfse_nacional.demo_nfse_lc")
        set_provedor_nacional(cls.document)
        cls.line = cls.document.fiscal_line_ids[0]

    def _xml(self):
        xml = self.document._serialize([])[0].to_xml()
        self.assertEqual(Dps.schema_validation(xml), [])
        return xml

    def test_a_taxable_service_has_no_comext(self):
        self.line.issqn_eligibility = "1"
        self.assertFalse(self.line.nfse10_comExt)
        self.assertNotIn("<comExt>", self._xml())

    def test_an_exported_service_carries_comext_in_reais(self):
        self.line.issqn_eligibility = "4"
        xml = self._xml()
        self.assertIn("<tribISSQN>3</tribISSQN>", xml)
        self.assertIn("<comExt>", xml)
        self.assertIn("<mdPrestacao>1</mdPrestacao>", xml)
        self.assertIn("<vincPrest>0</vincPrest>", xml)
        self.assertIn("<tpMoeda>790</tpMoeda>", xml)
        self.assertIn(f"<vServMoeda>{self.line.nfse10_vServ}</vServMoeda>", xml)
        self.assertIn("<mecAFComexP>01</mecAFComexP>", xml)
        self.assertIn("<mecAFComexT>01</mecAFComexT>", xml)
        self.assertIn("<movTempBens>1</movTempBens>", xml)
        self.assertIn("<mdic>0</mdic>", xml)

    def test_the_mode_and_the_link_come_from_the_document(self):
        self.line.issqn_eligibility = "4"
        self.document.write(
            {
                "nfse_foreign_trade_mode": "4",
                "nfse_foreign_trade_link": "3",
                "nfse_foreign_trade_support_provider": "02",
                "nfse_foreign_trade_support_recipient": "14",
            }
        )
        xml = self._xml()
        self.assertIn("<mdPrestacao>4</mdPrestacao>", xml)
        self.assertIn("<vincPrest>3</vincPrest>", xml)
        self.assertIn("<mecAFComexP>02</mecAFComexP>", xml)
        self.assertIn("<mecAFComexT>14</mecAFComexT>", xml)

    def test_a_taker_abroad_asks_for_comext_even_when_taxable(self):
        self.line.issqn_eligibility = "1"
        self.document.partner_id.country_id = self.env.ref("base.us")
        self.assertTrue(self.line.nfse10_comExt)

    def test_an_invoice_in_foreign_currency_goes_in_reais(self):
        """vServ is in reais and the original amount goes to vServMoeda with the
        BACEN code of the currency."""
        self.line.issqn_eligibility = "4"
        usd = self.env.ref("base.USD")
        original = round(self.line.price_gross, 2)
        with mock.patch.object(
            type(self.document),
            "_nfse_foreign_currency_rate",
            return_value=(usd, 5.0),
        ):
            self.line.invalidate_recordset()
            self.assertEqual(self.line.nfse10_tpMoeda, "220")
            self.assertEqual(self.line.nfse10_vServMoeda, f"{original:.2f}")
            self.assertEqual(self.line.nfse10_vServ, f"{round(original * 5, 2):.2f}")
