# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from types import SimpleNamespace

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.l10n_br_sped_efd_pis_cofins.models.sped_efd_pis_cofins import (
    COD_REC,
    _detail_vals,
)


@tagged("post_install", "-at_install")
class TestSpedPisCofinsM210(TransactionCase):
    """The detail of the contribution (M210, M610) and the revenue code (M205)."""

    def _detail(self, rate_field, base, tax):
        declaration = SimpleNamespace(
            company_id=SimpleNamespace(
                piscofins_id=self.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo")
            )
        )
        record = SimpleNamespace(
            assessment_id=SimpleNamespace(regime="cumulative"),
            base_amount=base,
            tax_amount=tax,
            tax_id=SimpleNamespace(
                fiscal_tax_ids=self.env["l10n_br_fiscal.tax"], amount=0.0
            ),
        )
        return _detail_vals(record, rate_field, declaration)

    def test_the_rate_comes_from_the_regime_and_the_base_closes_with_it(self):
        """The PVA demands VL_CONT_APUR = base x rate and a rate in the detail:
        the account tax carries none, so it is the one of the PIS/COFINS regime
        of the company."""
        pis = self._detail("ALIQ_PIS", 843.5, 6.5)
        self.assertEqual(pis["ALIQ_PIS"], 0.65)
        self.assertAlmostEqual(pis["VL_BC_CONT"] * pis["ALIQ_PIS"] / 100, 6.5, 2)
        cofins = self._detail("ALIQ_COFINS", 843.5, 30.0)
        self.assertEqual(cofins["ALIQ_COFINS"], 3.0)
        self.assertAlmostEqual(
            cofins["VL_BC_CONT"] * cofins["ALIQ_COFINS"] / 100, 30.0, 2
        )

    def test_the_revenue_code_has_the_six_positions_of_the_table(self):
        for code in COD_REC.values():
            self.assertEqual(len(code), 6, code)
        self.assertEqual(COD_REC[("pis", "cumulative")], "810902")
