# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_credito import CreditMixin

JULY = date(2026, 7, 10)
AUGUST = date(2026, 8, 10)


@tagged("post_install", "-at_install")
class TestSpedPisCofinsCreditBalance(CreditMixin, SpedEntradaCommon):
    """The credit that is left of a month is used in the next ones, oldest first,
    and the registers 1100 (PIS) and 1500 (COFINS) control it."""

    profit_calculation = "real"

    def _declaration_month(self, month):
        last = 31 if month in (7, 8) else 30
        return self._declaration(
            "efd_pis_cofins", date(2026, month, 1), date(2026, month, last)
        )

    def _first_month(self):
        """Credit above the contribution: a resale and an input (credit PIS 33.00,
        COFINS 152.00) and a sale (PIS 16.50, COFINS 76.00): the balance is PIS
        16.50 and COFINS 76.00."""
        self._entry("fo_compras_compras_comercializacao", "401", JULY)
        self._entry("fo_compras_compras", "402", JULY)
        self._sale(date(2026, 7, 12))
        self._assess("pis", month=7)
        self._assess("cofins", month=7)

    def _second_month(self, sales):
        """A resale (credit PIS 16.50) and the given number of sales."""
        self._entry("fo_compras_compras_comercializacao", "403", AUGUST)
        for _index in range(sales):
            self._sale(date(2026, 8, 12))
        self._assess("pis", month=8)
        self._assess("cofins", month=8)

    def test_the_first_month_leaves_the_balance(self):
        self._first_month()
        declaration = self._declaration_month(7)
        self.assertEqual(self._sped_records(declaration, "1100"), [])
        m100 = self._sped_records(declaration, "M100")[0]
        self.assertEqual(m100["VL_CRED_DESC"], "16,50")
        self.assertEqual(m100["SLD_CRED"], "16,50")

    def test_the_balance_of_the_month_goes_to_the_1100_and_is_used_first(self):
        """Contribution above what the two credits cover: the balance of July is
        used first (1100 and the field of the credit of earlier periods of the
        M200), then the credit of August (M100)."""
        self._first_month()
        self._second_month(sales=3)
        declaration = self._declaration_month(8)
        r1100 = self._sped_records(declaration, "1100")
        self.assertEqual(len(r1100), 1)
        self.assertEqual(r1100[0]["PER_APU_CRED"], "072026")
        self.assertEqual(r1100[0]["ORIG_CRED"], "01")
        self.assertEqual(r1100[0]["COD_CRED"], "101")
        self.assertEqual(r1100[0]["VL_CRED_APU"], "33,00")
        self.assertEqual(r1100[0]["VL_TOT_CRED_APU"], "33,00")
        self.assertEqual(r1100[0]["VL_CRED_DESC_PA_ANT"], "16,50")
        self.assertEqual(r1100[0]["SD_CRED_DISP_EFD"], "16,50")
        self.assertEqual(r1100[0]["VL_CRED_DESC_EFD"], "16,50")
        self.assertEqual(r1100[0]["SLD_CRED_FIM"], "0")
        m100 = self._sped_records(declaration, "M100")[0]
        self.assertEqual(m100["VL_CRED"], "16,50")
        self.assertEqual(m100["IND_DESC_CRED"], "0")
        self.assertEqual(m100["VL_CRED_DESC"], "16,50")
        m200 = self._sped_records(declaration, "M200")[0]
        self.assertEqual(m200["VL_TOT_CONT_NC_PER"], "49,50")
        self.assertEqual(m200["VL_TOT_CRED_DESC"], "16,50")
        self.assertEqual(m200["VL_TOT_CRED_DESC_ANT"], "16,50")
        self.assertEqual(m200["VL_TOT_CONT_NC_DEV"], "16,50")
        # the COFINS follows the same chain
        r1500 = self._sped_records(declaration, "1500")
        self.assertEqual(len(r1500), 1)
        self.assertEqual(r1500[0]["VL_CRED_DESC_EFD"], "76,00")
        m600 = self._sped_records(declaration, "M600")[0]
        self.assertEqual(m600["VL_TOT_CRED_DESC"], "76,00")
        self.assertEqual(m600["VL_TOT_CRED_DESC_ANT"], "76,00")
        self.assertEqual(m600["VL_TOT_CONT_NC_DEV"], "76,00")

    def test_the_credit_of_the_month_is_what_is_left_of_the_balance(self):
        """One sale only: it takes the balance of July and the credit of August
        stays, partly used (none), as the new balance."""
        self._first_month()
        self._second_month(sales=1)
        declaration = self._declaration_month(8)
        r1100 = self._sped_records(declaration, "1100")[0]
        self.assertEqual(r1100["VL_CRED_DESC_EFD"], "16,50")
        self.assertEqual(r1100["SLD_CRED_FIM"], "0")
        m100 = self._sped_records(declaration, "M100")[0]
        self.assertEqual(self._number(m100["VL_CRED_DESC"]), 0.0)
        self.assertEqual(m100["IND_DESC_CRED"], "1")
        self.assertEqual(m100["SLD_CRED"], "16,50")
        m200 = self._sped_records(declaration, "M200")[0]
        self.assertEqual(m200["VL_TOT_CRED_DESC_ANT"], "16,50")
        self.assertEqual(self._number(m200["VL_TOT_CONT_NC_DEV"]), 0.0)

    def test_the_file_stops_when_an_earlier_month_was_never_assessed(self):
        """June has credit and no assessment at all; July is assessed and posted.
        The balance of July starts from zero and the credit of June would be lost
        without a word: the generation stops and says which month is missing."""
        self.company.tax_assessment_start = date(2026, 6, 1)
        self._entry("fo_compras_compras_comercializacao", "401", date(2026, 6, 10))
        self._entry("fo_compras_compras", "402", date(2026, 7, 10))
        self._sale(date(2026, 7, 12))
        self._assess("pis", month=7)
        self._assess("cofins", month=7)
        self._set_accountant()
        declaration = self._declaration_month(7)
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("06/2026", error.exception.args[0])
        self.assertIn("Faltam as apurações lançadas", error.exception.args[0])
