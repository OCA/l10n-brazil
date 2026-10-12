# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree
from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.tests.common import TransactionCase, tagged

from .common import set_provedor_nacional

NAMESPACE = "http://www.sped.fazenda.gov.br/nfse"


def _find(root, path):
    if isinstance(root, str):
        root = etree.fromstring(root.encode())
    found = root.findall(path, namespaces={"nfse": NAMESPACE})
    return found[0] if found else None


# The import/export builds the spec models on the fly, which must not happen
# inside an at_install test transaction: it would roll back their tables.
@tagged("post_install", "-at_install")
class TestNfseIbscbs(TransactionCase):
    """The IBSCBS group of the DPS (leiaute 1.01, RTC) fed by the line taxes."""

    def setUp(self):
        super().setUp()
        self.nfse = self.env.ref(
            "l10n_br_nfse_nacional.demo_nfse_lc", raise_if_not_found=False
        )
        if not self.nfse:
            self.skipTest("l10n_br_nfse_nacional demo data is not installed")
        set_provedor_nacional(self.nfse)
        self.line = self.nfse.fiscal_line_ids[0]
        # the RTC data of a taxed service: cClassTrib and the IBS CST come
        # from the fiscal engine, the cIndOp from the RTC table
        self.line.tax_classification_id = self.env.ref(
            "l10n_br_fiscal.tax_classification_000001"
        )
        self.line.ibs_cst_id = self.env.ref("l10n_br_fiscal.cst_ibs_000")
        self.nfse.nfse10_cIndOp_id = self.env.ref(
            "l10n_br_fiscal.operation_indicator_030101"
        )

    def _export_ibscbs(self):
        """Build the IBSCBS group through the framework per tag hooks."""
        return self.nfse.with_context(
            spec_schema="nfse", spec_version="10"
        )._export_m2o_via_tag_hooks("nfse10_IBSCBS", self.env["nfse.10.tcinfdps"])

    def test_export_ibscbs(self):
        ibscbs = self._export_ibscbs()
        self.assertTrue(ibscbs)
        self.assertEqual(ibscbs.finNFSe, "0")
        self.assertEqual(ibscbs.cIndOp, "030101")
        self.assertEqual(ibscbs.indDest, "0")
        self.assertEqual(ibscbs.valores.trib.gIBSCBS.CST, "000")
        self.assertEqual(ibscbs.valores.trib.gIBSCBS.cClassTrib, "000001")

    def test_export_ibscbs_cbs_cst_fallback(self):
        """A CBS only line still exports the single CST of the DPS group."""
        self.line.ibs_cst_id = False
        self.line.cbs_cst_id = self.env.ref("l10n_br_fiscal.cst_cbs_000")
        ibscbs = self._export_ibscbs()
        self.assertTrue(ibscbs)
        self.assertEqual(ibscbs.valores.trib.gIBSCBS.CST, "000")

    def test_export_ibscbs_without_rtc_classification(self):
        self.line.tax_classification_id = False
        self.assertFalse(self._export_ibscbs())

    def test_export_ibscbs_without_operation_indicator(self):
        self.nfse.nfse10_cIndOp_id = False
        self.assertFalse(self._export_ibscbs())

    def test_export_ibscbs_without_cst(self):
        self.line.ibs_cst_id = False
        self.line.cbs_cst_id = False
        self.assertFalse(self._export_ibscbs())

    def test_dps_ibscbs_group(self):
        """The serialized DPS carries the RTC group of the line."""
        xml = self.nfse._serialize([])[0].to_xml()

        ibscbs = _find(xml, "./nfse:infDPS/nfse:IBSCBS")
        self.assertIsNotNone(ibscbs)
        self.assertEqual(
            _find(xml, "./nfse:infDPS/nfse:IBSCBS/nfse:cIndOp").text, "030101"
        )
        self.assertEqual(_find(xml, "./nfse:infDPS/nfse:IBSCBS/nfse:indDest").text, "0")
        gibscbs = _find(
            xml,
            "./nfse:infDPS/nfse:IBSCBS/nfse:valores/nfse:trib/nfse:gIBSCBS",
        )
        self.assertEqual(_find(gibscbs, "./nfse:CST").text, "000")
        self.assertEqual(_find(gibscbs, "./nfse:cClassTrib").text, "000001")

    def test_dps_without_rtc_data_has_no_ibscbs(self):
        """A DPS with no RTC data keeps the legacy 1.00 shape."""
        self.line.tax_classification_id = False
        xml = self.nfse._serialize([])[0].to_xml()
        self.assertIsNone(_find(xml, "./nfse:infDPS/nfse:IBSCBS"))

    def test_dps_with_ibscbs_validates_against_the_101_schema(self):
        xml = self.nfse._serialize([])[0].to_xml()
        self.assertTrue(Dps._get_schema_path().endswith("DPS_v1.01.xsd"))
        self.assertEqual(Dps.schema_validation(xml), [])
