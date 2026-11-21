# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_entrada import EntradaHelpers


@tagged("post_install", "-at_install")
class TestSpedEntradaCreditoIcms(EntradaHelpers, SpedEntradaCommon):
    """The ICMS credit of the assessment (E110) is the one of the entry C190.

    The assessment reads the ledger and the C190 reads the fiscal line, so both
    have to ask the company the same question. A company that books its
    entries by the creditability map leaves the ICMS of use and consumption
    (CFOP 1556/2556, LC 87/1996, art. 33, I) out of both; any other credits it
    in both. The PVA crosses E110 field 5 with the C190.
    """

    @staticmethod
    def _product_line(move):
        return move.invoice_line_ids.filtered("product_id")

    def _icms_lines(self, move):
        return move.line_ids.filtered(
            lambda line: line.tax_line_id.tax_group_id.fiscal_tax_group_id.tax_domain
            == "icms"
        )

    def _e110_and_c190(self):
        self._assess_icms_of_july()
        declaration = self._declaration_july()
        c190 = {
            rec["CFOP"]: rec
            for rec in self._sped_records(declaration, "C190")
            if rec["CFOP"].startswith(("1", "2", "3"))
        }
        e110 = self._sped_records(declaration, "E110")
        self.assertEqual(len(e110), 1)
        credit = self._number(e110[0]["VL_TOT_CREDITOS"])
        self.assertAlmostEqual(
            credit,
            sum(self._number(rec["VL_ICMS"]) for rec in c190.values()),
            places=2,
        )
        return credit, c190

    def test_e110_credit_of_a_use_and_consumption_purchase(self):
        self._opt_in()
        resale = self._purchase_move("fo_compras_compras_comercializacao", "801")
        consumption = self._purchase_move("fo_compras_compras_uso_consumo", "802")
        consumption_line = self._product_line(consumption)
        self.assertIn(consumption_line.cfop_id.code, ("1556", "2556"))
        self.assertGreater(consumption_line.icms_value, 0, "the note has ICMS")
        self.assertFalse(self._icms_lines(consumption), "no ICMS to recover")
        self.assertTrue(self._icms_lines(resale))
        credit, c190 = self._e110_and_c190()
        self.assertEqual(c190[consumption_line.cfop_id.code]["CST_ICMS"][1:], "90")
        self.assertAlmostEqual(credit, self._product_line(resale).icms_value, places=2)

    def test_e110_credit_of_a_company_that_did_not_opt_in(self):
        """The case the PVA refused: the ledger credited the ICMS of use and
        consumption while the C190 carried it without credit."""
        self._opt_in(False)
        resale = self._purchase_move("fo_compras_compras_comercializacao", "811")
        consumption = self._purchase_move("fo_compras_compras_uso_consumo", "812")
        consumption_line = self._product_line(consumption)
        self.assertIn(consumption_line.cfop_id.code, ("1556", "2556"))
        icms = self._icms_lines(consumption)
        self.assertAlmostEqual(
            sum(icms.mapped("balance")), consumption_line.icms_value, places=2
        )
        credit, c190 = self._e110_and_c190()
        consumption_c190 = c190[consumption_line.cfop_id.code]
        self.assertNotEqual(consumption_c190["CST_ICMS"][1:], "90")
        self.assertAlmostEqual(
            self._number(consumption_c190["VL_ICMS"]),
            consumption_line.icms_value,
            places=2,
        )
        self.assertAlmostEqual(
            self._number(consumption_c190["VL_IPI"]),
            consumption_line.ipi_value,
            places=2,
        )
        self.assertAlmostEqual(
            credit,
            self._product_line(resale).icms_value + consumption_line.icms_value,
            places=2,
        )
