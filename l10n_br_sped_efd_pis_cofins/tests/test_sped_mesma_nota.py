# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import date

from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_credito import CreditMixin

C170_FIELDS = (
    "CST_ICMS",
    "VL_BC_ICMS",
    "ALIQ_ICMS",
    "VL_ICMS",
    "CST_IPI",
    "VL_BC_IPI",
    "ALIQ_IPI",
    "VL_IPI",
)
C100_FIELDS = ("VL_BC_ICMS", "VL_ICMS", "VL_IPI", "VL_PIS", "VL_COFINS")


@tagged("post_install", "-at_install")
class TestSpedTheSameNoteInTheTwoFiles(CreditMixin, SpedEntradaCommon):
    """The EFD ICMS/IPI and the EFD Contribuicoes carry the same entry the same
    way: one function, the one of the base, says the ICMS and the IPI of the line
    as the books carry them."""

    profit_calculation = "real"

    def setUp(self):
        super().setUp()
        self._opt_in_entry_without_credit()

    def _both(self, operation_line, number):
        if "l10n_br_sped.efd_icms_ipi.0000" not in self.env:
            self.skipTest("the EFD ICMS/IPI is not installed")
        self._entry(operation_line, number)
        icms = self._declaration("efd_icms_ipi", date(2026, 7, 1), date(2026, 7, 31))
        contrib = self._declaration_july()
        return icms, contrib

    def _compare(self, icms, contrib):
        c170_icms = self._sped_records(icms, "C170")
        c170_contrib = self._sped_records(contrib, "C170")
        self.assertEqual(len(c170_icms), 1)
        self.assertEqual(len(c170_contrib), 1)
        for name in C170_FIELDS:
            self.assertEqual(
                self._number_or_text(c170_icms[0][name]),
                self._number_or_text(c170_contrib[0][name]),
                name,
            )
        c100_icms = self._sped_records(icms, "C100")[0]
        c100_contrib = self._sped_records(contrib, "C100")[0]
        for name in C100_FIELDS:
            self.assertEqual(
                self._number_or_text(c100_icms[name]),
                self._number_or_text(c100_contrib[name]),
                name,
            )
        # the header of the document is what the items carry, in each file
        for register, c170_list, c100 in (
            ("EFD ICMS/IPI", c170_icms, c100_icms),
            ("EFD Contribuicoes", c170_contrib, c100_contrib),
        ):
            for total, item in (("VL_PIS", "VL_PIS"), ("VL_COFINS", "VL_COFINS")):
                self.assertAlmostEqual(
                    self._number(c100[total]),
                    sum(self._number(rec[item]) for rec in c170_list),
                    places=2,
                    msg=f"{register} {total}",
                )
        return c170_contrib[0], c100_contrib

    @staticmethod
    def _number_or_text(text):
        try:
            return float(text.replace(",", ".") or 0)
        except ValueError:
            return text

    def test_the_use_and_consumption_entry_is_the_same_in_the_two_files(self):
        """ICMS CST 90 and IPI CST 49, no base, rate or value, in the C170 and in
        the totals of the C100 of the two files."""
        icms, contrib = self._both("fo_compras_compras_uso_consumo", "403")
        c170, c100 = self._compare(icms, contrib)
        self.assertTrue(c170["CST_ICMS"].endswith("90"))
        self.assertEqual(self._number(c170["VL_ICMS"]), 0.0)
        self.assertEqual(c170["CST_IPI"], "49")
        self.assertEqual(self._number(c170["VL_IPI"]), 0.0)
        self.assertEqual(self._number(c100["VL_ICMS"]), 0.0)
        self.assertEqual(self._number(c100["VL_IPI"]), 0.0)
        self.assertEqual(self._number(c100["VL_PIS"]), 0.0)
        self.assertEqual(self._number(c100["VL_COFINS"]), 0.0)

    def test_the_resale_entry_is_the_same_in_the_two_files(self):
        """The credit entry keeps its ICMS and IPI in both."""
        icms, contrib = self._both("fo_compras_compras_comercializacao", "401")
        c170, c100 = self._compare(icms, contrib)
        self.assertGreater(self._number(c170["VL_ICMS"]), 0.0)
        self.assertGreater(self._number(c100["VL_ICMS"]), 0.0)
