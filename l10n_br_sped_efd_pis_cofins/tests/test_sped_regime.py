# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_credito import CreditMixin


@tagged("post_install", "-at_install")
class TestSpedPisCofinsContributionCode(CreditMixin, SpedEntradaCommon):
    """The code of the contribution (M210 and M610) of a company whose tax group
    does not say the regime: the regime of the company."""

    def test_the_cumulative_code_comes_from_the_company(self):
        self._entry("fo_compras_compras_comercializacao", "401")
        self._sale()
        pis = self._assess("pis", regime="not_applicable")
        self._assess("cofins", regime="not_applicable")
        self.assertEqual(pis.tax_group_id.regime, "not_applicable")
        self.assertEqual(pis.regime, "cumulative")
        declaration = self._declaration_july()
        self.assertEqual(self._sped_records(declaration, "M210")[0]["COD_CONT"], "51")
        self.assertEqual(self._sped_records(declaration, "M610")[0]["COD_CONT"], "51")

    def test_the_generation_stops_when_the_code_cannot_be_determined(self):
        """No code is worse than a message: the M210 went out as |M210||..."""
        self._entry("fo_compras_compras_comercializacao", "401")
        self._sale()
        pis = self._assess("pis", regime="not_applicable")
        self._assess("cofins", regime="not_applicable")
        self.env.cr.execute(
            "UPDATE l10n_br_tax_assessment SET regime = 'not_applicable' "
            "WHERE id = %s",
            (pis.id,),
        )
        pis.invalidate_recordset(["regime"])
        self._set_accountant()
        declaration = self._declaration_july()
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("contribution code", error.exception.args[0])


@tagged("post_install", "-at_install")
class TestSpedPisCofinsContributionCodeReal(CreditMixin, SpedEntradaCommon):
    profit_calculation = "real"

    def test_the_non_cumulative_code_comes_from_the_company(self):
        self._entry("fo_compras_compras_comercializacao", "401")
        self._sale()
        pis = self._assess("pis", regime="not_applicable")
        self._assess("cofins", regime="not_applicable")
        self.assertEqual(pis.regime, "non_cumulative")
        declaration = self._declaration_july()
        self.assertEqual(self._sped_records(declaration, "M210")[0]["COD_CONT"], "01")
        self.assertEqual(self._sped_records(declaration, "M610")[0]["COD_CONT"], "01")
