# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase

# "None of the above" CSTs: presuming a credit there has no legal ground.
RESIDUAL_CSTS = (
    ("l10n_br_fiscal.cst_icms_90", "ICMS 90 Outras"),
    ("l10n_br_fiscal.cst_ipi_49", "IPI 49 Outras entradas"),
    ("l10n_br_fiscal.cst_pis_98", "PIS 98 Outras Operacoes de Entrada"),
    ("l10n_br_fiscal.cst_cofins_98", "COFINS 98 Outras Operacoes de Entrada"),
    ("l10n_br_fiscal.cst_icmssn_900", "CSOSN 900 Outros"),
)

# CSTs that grant an input credit by nature, with the rule that grants it.
CREDITABLE_CSTS = (
    ("l10n_br_fiscal.cst_icms_00", "LC 87/96 art. 20, fully taxed"),
    ("l10n_br_fiscal.cst_icms_20", "LC 87/96 art. 20, reduced base"),
    ("l10n_br_fiscal.cst_ipi_00", "RIPI art. 226, entry with credit"),
    ("l10n_br_fiscal.cst_icmssn_101", "LC 123/2006 art. 23, par. 1"),
)


class TestCstCreditable(TransactionCase):
    """The CST states whether an operation allows an input credit by nature."""

    def test_field_default_is_conservative(self):
        """A CST created without stating anything takes no credit."""
        cst = self.env["l10n_br_fiscal.cst"].new({})
        self.assertFalse(cst.default_creditable_tax)

    def test_residual_csts_take_no_credit(self):
        for xml_id, label in RESIDUAL_CSTS:
            cst = self.env.ref(xml_id)
            self.assertFalse(
                cst.default_creditable_tax,
                f"{label} is residual and must not presume a credit",
            )

    def test_creditable_csts_keep_their_credit(self):
        for xml_id, rule in CREDITABLE_CSTS:
            cst = self.env.ref(xml_id)
            self.assertTrue(
                cst.default_creditable_tax,
                f"{cst.code} grants a credit by {rule}",
            )
