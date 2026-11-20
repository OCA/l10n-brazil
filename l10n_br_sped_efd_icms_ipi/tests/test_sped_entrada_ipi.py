# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_entrada import EntradaHelpers


@tagged("post_install", "-at_install")
class TestSpedEfdIcmsIpiIpiEntrada(EntradaHelpers, SpedEntradaCommon):
    """Own issue and the registers nothing refers to in the books."""

    def test_an_nfe_issued_by_the_company_has_no_c170(self):
        """The Guia Pratico: C100 and C190 only for an own issue."""
        sale, _line = self._entry_document(
            operation="fo_venda", operation_line="fo_venda_venda", imported=False
        )
        declaration = self._declaration_july()
        self.assertIn(sale.document_number, self._c100(declaration))
        self.assertEqual(self._sped_records(declaration, "C170"), [])
        self.assertTrue(self._sped_records(declaration, "C190"))

    def test_no_0450_without_a_register_that_refers_to_it(self):
        """The PVA refuses a 0450 that nothing points to."""
        doc, _line = self._entry_document()
        doc.comment_ids = [
            (6, 0, self.env["l10n_br_fiscal.comment"].search([], limit=1).ids)
        ]
        declaration = self._declaration_july()
        self.assertEqual(self._sped_records(declaration, "0450"), [])

    def test_0400_only_lists_the_natures_an_item_points_to(self):
        """The natureza of an own issue (no C170) is not declared: the PVA
        refuses a 0400 that no register refers to."""
        self._entry_document()
        self._entry_document(
            operation="fo_venda", operation_line="fo_venda_venda", imported=False
        )
        declaration = self._declaration_july()
        codes = [rec["COD_NAT"] for rec in self._sped_records(declaration, "0400")]
        self.assertEqual(codes, [self.env.ref("l10n_br_fiscal.fo_compras").code])
