# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestTaxableUnit(TransactionCase):
    def setUp(self):
        super().setUp()
        self.unit = self.env.ref("uom.product_uom_unit")
        self.kg = self.env.ref("uom.product_uom_kgm")
        self.meter = self.env.ref("uom.product_uom_meter")
        self.gram = self.env.ref("uom.product_uom_gram")
        self.ncm = self.env["l10n_br_fiscal.ncm"].create(
            {"code": "9999.99.99", "name": "NCM de teste", "uot_id": self.kg.id}
        )
        self.product = self.env["product.product"].create(
            {
                "name": "Produto de teste",
                "uom_id": self.unit.id,
                "uot_factor": 50.0,
            }
        )

    def _line(self, **values):
        return self.env["l10n_br_fiscal.document.line"].new(
            dict({"product_id": self.product.id, "uom_id": self.unit.id}, **values)
        )

    def test_the_taxable_unit_falls_back_to_the_ncm(self):
        """Rejection 817 is what happens when it does not.

        The uTrib has to follow the unit the SEFAZ table fixes for the NCM, and
        the commercial unit of the product has nothing to do with it. The error
        only shows up after transmitting, so the wrong unit travels silently.
        """
        line = self._line(ncm_id=self.ncm.id)

        self.assertEqual(line.uot_id, self.kg)

    def test_quantity_and_price_follow_the_unit_from_the_ncm(self):
        """10 bags of 50 kg at 35.00 are 500 kg at 0.70, and the total holds."""
        line = self._line(ncm_id=self.ncm.id, quantity=10, price_unit=35.0)

        self.assertEqual(line.uot_id, self.kg)
        self.assertAlmostEqual(line.fiscal_quantity, 500.0)
        self.assertAlmostEqual(line.fiscal_price, 0.70)

    def test_units_of_the_same_category_are_converted_by_odoo(self):
        """No factor is needed when Odoo already relates the two units."""
        self.product.write({"uom_id": self.gram.id, "uot_factor": 0.0})

        line = self._line(
            ncm_id=self.ncm.id, uom_id=self.gram.id, quantity=2000, price_unit=0.01
        )

        self.assertEqual(line.uot_id, self.kg)
        self.assertAlmostEqual(line.fiscal_quantity, 2.0)
        self.assertAlmostEqual(line.fiscal_price, 10.0)

    def test_without_a_conversion_the_commercial_unit_is_kept(self):
        """Declaring kg with the quantity in bags would be wrong, so it is not."""
        self.product.uot_factor = 0.0

        line = self._line(ncm_id=self.ncm.id, quantity=10, price_unit=35.0)

        self.assertEqual(line.uot_id, self.unit)
        self.assertAlmostEqual(line.fiscal_quantity, 10.0)
        self.assertAlmostEqual(line.fiscal_price, 35.0)

    def test_the_unit_on_the_product_wins_over_the_ncm(self):
        self.product.uot_id = self.meter

        line = self._line(ncm_id=self.ncm.id)

        self.assertEqual(line.uot_id, self.meter)

    def test_without_an_ncm_unit_the_commercial_one_is_kept(self):
        self.ncm.uot_id = False

        line = self._line(ncm_id=self.ncm.id)

        self.assertEqual(line.uot_id, self.unit)
