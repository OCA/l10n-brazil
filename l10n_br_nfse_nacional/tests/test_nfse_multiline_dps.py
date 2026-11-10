# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unittest

from lxml import etree
from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from .common import set_provedor_nacional

NAMESPACE = "http://www.sped.fazenda.gov.br/nfse"


def _find(root, path):
    if isinstance(root, str):
        root = etree.fromstring(root.encode())
    found = root.findall(path, namespaces={"nfse": NAMESPACE})
    return found[0] if found else None


# The export builds the remaining spec models on the fly, which must not happen
# inside an at_install test transaction: it would roll back their tables.
@tagged("post_install", "-at_install")
class TestNfseMultilineDps(TransactionCase):
    """A DPS declares a single service: its whole document is declared as one."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document = cls.env.ref(
            "l10n_br_nfse_nacional.demo_nfse_lc", raise_if_not_found=False
        )
        if not cls.document:
            raise unittest.SkipTest("l10n_br_nfse_nacional demo data is not installed")
        set_provedor_nacional(cls.document)
        cls.code = cls.env.ref("l10n_br_nfse_nacional.nat_tax_code_010101")
        # The national taxation code of the line comes from the product, so the
        # services are declared by their products, like a real invoice does.
        cls.product = cls.env["product.product"].create(
            {
                "name": "Desenvolvimento de software",
                "type": "service",
                "tax_icms_or_issqn": "issqn",
                "national_taxation_code_id": cls.code.id,
            }
        )
        cls.document.fiscal_line_ids.unlink()
        cls.line_a = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "product_id": cls.product.id,
                "name": "Desenvolvimento de software",
                "price_unit": 100.0,
                "quantity": 1,
                "discount_value": 10.0,
                "issqn_desc_cond_amount": 5.0,
            }
        )
        cls.line_b = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "product_id": cls.product.id,
                "name": "Sustentação mensal",
                "price_unit": 60.0,
                "quantity": 1,
            }
        )
        # the withheld amounts are the last written: any further write on the
        # amounts recomputes the taxes of the line
        cls.line_a.write({"inss_wh_value": 1.5, "irpj_wh_value": 1.0})
        cls.line_b.write({"inss_wh_value": 0.5})

    def _set_concat_lines(self, value):
        self.document.company_id.nfse_nacional_concat_lines = value

    def _serialize(self):
        return self.document._serialize([])[0].to_xml()

    def test_all_lines_declared_as_one_service(self):
        """The single service sums the amounts and joins the descriptions."""
        self._set_concat_lines(True)
        xml = self._serialize()
        self.assertEqual(Dps.schema_validation(xml), [])
        self.assertEqual(xml.count("<cServ>"), 1)
        self.assertEqual(
            _find(xml, "./nfse:infDPS/nfse:serv/nfse:cServ/nfse:cTribNac").text,
            "010101",
        )
        valores = "./nfse:infDPS/nfse:valores"
        self.assertEqual(
            _find(xml, f"{valores}/nfse:vServPrest/nfse:vServ").text, "160.00"
        )
        desc = _find(xml, "./nfse:infDPS/nfse:serv/nfse:cServ/nfse:xDescServ").text
        self.assertIn("Desenvolvimento de software", desc)
        self.assertIn("Sustentação mensal", desc)
        # the discounts and the withholdings are summed as well
        self.assertEqual(
            _find(xml, f"{valores}/nfse:vDescCondIncond/nfse:vDescIncond").text,
            "10.00",
        )
        self.assertEqual(
            _find(xml, f"{valores}/nfse:vDescCondIncond/nfse:vDescCond").text, "5.00"
        )
        trib_fed = f"{valores}/nfse:trib/nfse:tribFed"
        self.assertEqual(_find(xml, f"{trib_fed}/nfse:vRetCP").text, "2.00")
        self.assertEqual(_find(xml, f"{trib_fed}/nfse:vRetIRRF").text, "1.00")

    def test_first_line_only_by_default(self):
        """Without the option the legacy single line export is kept."""
        self._set_concat_lines(False)
        xml = self._serialize()
        self.assertEqual(Dps.schema_validation(xml), [])
        self.assertEqual(
            _find(xml, "./nfse:infDPS/nfse:valores/nfse:vServPrest/nfse:vServ").text,
            "100.00",
        )
        self.assertEqual(
            _find(xml, "./nfse:infDPS/nfse:serv/nfse:cServ/nfse:xDescServ").text,
            "Desenvolvimento de software",
        )

    def test_lines_with_different_taxation_codes_are_refused(self):
        """Two services cannot be declared as one: the DPS is refused."""
        self._set_concat_lines(True)
        other_code = self.env["l10n_br_fiscal.national.taxation.code"].create(
            {"name": "01.07.01", "code": "010701"}
        )
        other_product = self.env["product.product"].create(
            {
                "name": "Consultoria em TI",
                "type": "service",
                "tax_icms_or_issqn": "issqn",
                "national_taxation_code_id": other_code.id,
            }
        )
        self.line_b.product_id = other_product
        with self.assertRaises(UserError) as error:
            self._serialize()
        message = str(error.exception)
        self.assertIn("010101", message)
        self.assertIn("010701", message)

    def test_different_rtc_classification_is_refused(self):
        """A single RTC classification cannot describe two services either."""
        self._set_concat_lines(True)
        classification = self.env["l10n_br_fiscal.tax.classification"]
        self.document.fiscal_line_ids.tax_classification_id = classification.search(
            [], limit=1
        )
        self.line_b.tax_classification_id = classification.search([], limit=1, offset=1)
        with self.assertRaises(UserError) as error:
            self._serialize()
        self.assertIn("cClassTrib", str(error.exception))

    def test_long_description_is_truncated(self):
        """xDescServ is capped at 2000 characters, and never left blank."""
        self._set_concat_lines(True)
        self.line_a.name = "Desenvolvimento " + "d" * 1185
        self.line_b.name = "Sustentação " + "s" * 1187
        self.assertTrue(len(f"{self.line_a.name}\n{self.line_b.name}") > 2000)
        xml = self._serialize()
        self.assertEqual(Dps.schema_validation(xml), [])
        desc = _find(xml, "./nfse:infDPS/nfse:serv/nfse:cServ/nfse:xDescServ").text
        self.assertEqual(len(desc), 2000)
        self.assertTrue(desc.strip())
        self.assertFalse(desc.endswith(" "))
