# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestTaxableUnit(TransactionCase):
    def setUp(self):
        super().setUp()
        self.unit = self.env.ref("uom.product_uom_unit")
        self.kg = self.env.ref("uom.product_uom_kgm")
        self.meter = self.env.ref("uom.product_uom_meter")
        self.ncm = self.env["l10n_br_fiscal.ncm"].create(
            {"code": "9999.99.99", "name": "NCM de teste", "uot_id": self.kg.id}
        )
        self.product = self.env["product.product"].create(
            {"name": "Produto de teste", "uom_id": self.unit.id}
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

    def test_the_unit_on_the_product_wins_over_the_ncm(self):
        self.product.uot_id = self.meter

        line = self._line(ncm_id=self.ncm.id)

        self.assertEqual(line.uot_id, self.meter)

    def test_without_an_ncm_unit_the_commercial_one_is_kept(self):
        self.ncm.uot_id = False

        line = self._line(ncm_id=self.ncm.id)

        self.assertEqual(line.uot_id, self.unit)
