# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import date
from pathlib import Path

from odoo.tests import TransactionCase

from ..wizards.declaration_xml import DeclarationXmlError, parse_declaration

FIXTURE = Path(__file__).parent / "fixtures" / "import_declaration.xml"


class TestDeclarationXml(TransactionCase):
    """Reading the declaration the Siscomex hands out.

    The fixture keeps the shape of a declaration of two additions and carries
    made up identifiers and made up amounts, coherent among themselves: the
    Import Tax follows the base, the IPI follows the base plus the Import Tax,
    and the goods add up to the value of their addition. That coherence is what
    the reading is proved against, because every number in the file is an
    integer with the decimals implied and the implied place changes by field,
    so a wrong scale gives a plausible number that is off by a factor of ten.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.declaration = parse_declaration(FIXTURE.read_bytes())

    def test_the_header_comes_out_whole(self):
        self.assertEqual(self.declaration["number"], "2600000001")
        self.assertEqual(self.declaration["registration_date"], date(2026, 7, 10))
        self.assertEqual(self.declaration["clearance_date"], date(2026, 7, 10))
        self.assertEqual(self.declaration["transport_via"], "7")
        self.assertEqual(self.declaration["clearance_state"], "SP")

    def test_the_customs_value_is_the_sum_of_the_bases_of_the_import_tax(self):
        total = sum(a["customs_value"] for a in self.declaration["additions"])
        self.assertAlmostEqual(total, 800000.00, places=2)

    def test_each_addition_keeps_its_own_rate(self):
        """The point of reading addition by addition: the rate changes."""
        by_number = {a["number"]: a for a in self.declaration["additions"]}
        self.assertEqual(by_number["001"]["ncm"], "8414.90.20")
        self.assertAlmostEqual(by_number["001"]["ii_rate"], 12.60, places=2)
        self.assertAlmostEqual(by_number["001"]["ipi_rate"], 3.25, places=2)
        self.assertEqual(by_number["002"]["ncm"], "8537.10.90")
        self.assertAlmostEqual(by_number["002"]["ii_rate"], 18.00, places=2)
        self.assertAlmostEqual(by_number["002"]["ipi_rate"], 9.75, places=2)

    def test_the_import_tax_of_an_addition_follows_its_base_and_rate(self):
        """Coherence of the fixture, and of any declaration: the amount charged
        is the base times the rate the addition carries."""
        for addition in self.declaration["additions"]:
            self.assertAlmostEqual(
                addition["ii_value"],
                addition["customs_value"] * addition["ii_rate"] / 100.0,
                places=2,
            )

    def test_the_tax_of_the_additions_adds_up_to_the_declaration(self):
        additions = self.declaration["additions"]
        self.assertAlmostEqual(
            sum(a["ii_value"] for a in additions), 141840.00, places=2
        )
        self.assertAlmostEqual(
            sum(a["ipi_value"] for a in additions), 88901.80, places=2
        )
        self.assertAlmostEqual(
            sum(a["pis_value"] for a in additions), 16800.00, places=2
        )
        self.assertAlmostEqual(
            sum(a["cofins_value"] for a in additions), 77200.00, places=2
        )
        self.assertAlmostEqual(self.declaration["icms_value"], 200000.00, places=2)

    def test_the_goods_of_an_addition_add_up_to_its_value_in_currency(self):
        """Quantity and unit value carry different scales, five and seven.

        Reading either with the scale of money gives a total that is off by
        orders of magnitude, and nothing else in the file catches it.
        """
        addition = self.declaration["additions"][0]
        total = sum(i["quantity"] * i["unit_value"] for i in addition["items"])
        self.assertAlmostEqual(total, 8000.00, places=2)

    def test_the_ncm_comes_out_the_way_the_catalog_writes_it(self):
        self.assertEqual(self.declaration["additions"][0]["ncm"], "8414.90.20")

    def test_the_description_loses_the_tail_the_siscomex_glues_to_it(self):
        description = self.declaration["additions"][0]["items"][0]["description"]
        self.assertNotIn("cClassTrib", description)
        self.assertNotIn("\r", description)
        self.assertEqual(description, "MERCADORIA 1 DA ADICAO 1")

    def test_the_weight_is_read_with_its_own_scale(self):
        self.assertAlmostEqual(self.declaration["net_weight"], 180.00, places=2)

    def test_a_file_that_is_not_a_declaration_is_refused(self):
        with self.assertRaises(DeclarationXmlError):
            parse_declaration(b"<outraCoisa><a/></outraCoisa>")

    def test_a_file_that_is_not_xml_is_refused(self):
        with self.assertRaises(DeclarationXmlError):
            parse_declaration(b"nao sou xml")
