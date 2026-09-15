# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase

# CSTs whose code means "none of the above". They carry the least information
# of the whole table, so presuming a credit there is the worst possible
# default: it would take the tax out of the stock acquisition cost with no
# legal ground (art. 301 RIR/2018 keeps non recoverable taxes in the cost).
RESIDUAL_CSTS = (
    ("l10n_br_fiscal.cst_icms_90", "ICMS 90 Outras"),
    ("l10n_br_fiscal.cst_ipi_49", "IPI 49 Outras entradas"),
    ("l10n_br_fiscal.cst_pis_98", "PIS 98 Outras Operacoes de Entrada"),
    ("l10n_br_fiscal.cst_cofins_98", "COFINS 98 Outras Operacoes de Entrada"),
    ("l10n_br_fiscal.cst_icmssn_900", "CSOSN 900 Outros"),
)

# CSTs that do grant an input credit by their own nature, each with the rule
# that grants it. Kept short on purpose: this is a regression guard for the
# data file, not a copy of the tax code.
CREDITABLE_CSTS = (
    ("l10n_br_fiscal.cst_icms_00", "LC 87/96 art. 20, fully taxed"),
    ("l10n_br_fiscal.cst_icms_20", "LC 87/96 art. 20, reduced base"),
    ("l10n_br_fiscal.cst_ipi_00", "RIPI art. 226, entry with credit"),
    ("l10n_br_fiscal.cst_icmssn_101", "LC 123/2006 art. 23, par. 1"),
)


class TestCstCreditable(TransactionCase):
    """The CST states whether an operation allows an input credit by nature."""

    def test_field_default_is_conservative(self):
        """A CST created without stating anything takes no credit.

        The field default is what a CST added later inherits, including the
        IBS and CBS codes of the tax reform. Failing closed keeps a tax in
        the acquisition cost until someone states it is recoverable.
        """
        cst = self.env["l10n_br_fiscal.cst"].new({})
        self.assertFalse(cst.default_creditable_tax)

    def test_residual_csts_take_no_credit(self):
        for xml_id, label in RESIDUAL_CSTS:
            cst = self.env.ref(xml_id, raise_if_not_found=False)
            if not cst:
                continue
            self.assertFalse(
                cst.default_creditable_tax,
                f"{label} is residual and must not presume a credit",
            )

    def test_creditable_csts_keep_their_credit(self):
        for xml_id, rule in CREDITABLE_CSTS:
            cst = self.env.ref(xml_id, raise_if_not_found=False)
            if not cst:
                continue
            self.assertTrue(
                cst.default_creditable_tax,
                f"{cst.code} grants a credit by {rule}",
            )
