# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_credito import CreditMixin


@tagged("post_install", "-at_install")
class TestRecomputeEntryCst(CreditMixin, SpedEntradaCommon):
    """The entry CST of an imported document still being typed can be recalculated
    by the current rule; a confirmed document is never touched."""

    profit_calculation = "real"

    def setUp(self):
        super().setUp()
        self._opt_in_entry_without_credit()

    def _old_entry(self, state_edoc="em_digitacao"):
        """An entry of use and consumption as the import left it before the rule
        of the destination: PIS and COFINS with the credit CST 50."""
        document, line = self._entry_document(
            operation_line="fo_compras_compras_uso_consumo", state_edoc=state_edoc
        )
        self.assertEqual(line.entry_pis_cst_id.code, "70")
        line.write(
            {
                "entry_pis_cst_id": self.env.ref("l10n_br_fiscal.cst_pis_50").id,
                "entry_cofins_cst_id": self.env.ref("l10n_br_fiscal.cst_cofins_50").id,
            }
        )
        return document, line

    def test_the_button_recalculates_the_cst_and_says_what_changed(self):
        document, line = self._old_entry()
        document.action_recompute_entry_cst()
        self.assertEqual(line.entry_pis_cst_id.code, "70")
        self.assertEqual(line.entry_cofins_cst_id.code, "70")
        body = " ".join(document.message_ids.mapped("body"))
        self.assertIn("CST of the PIS: 50 to 70", body)
        self.assertIn("CST of the COFINS: 50 to 70", body)

    def test_a_confirmed_document_is_never_touched(self):
        document, line = self._old_entry(state_edoc="autorizada")
        with self.assertRaises(UserError):
            document.action_recompute_entry_cst()
        self.assertEqual(line.entry_pis_cst_id.code, "50")

    def test_the_list_action_only_takes_the_documents_in_typing(self):
        typing, typing_line = self._old_entry()
        confirmed, confirmed_line = self._old_entry(state_edoc="autorizada")
        (typing | confirmed).action_recompute_entry_cst_selection()
        self.assertEqual(typing_line.entry_pis_cst_id.code, "70")
        self.assertEqual(confirmed_line.entry_pis_cst_id.code, "50")

    def test_the_stop_of_the_credit_points_to_the_button_in_a_draft(self):
        document, line = self._old_entry()
        with self.assertRaises(UserError) as error:
            line._sped_credit("pis")
        self.assertIn("Recalculate Entry CST", error.exception.args[0])

    def test_the_stop_of_the_credit_of_a_confirmed_document_has_no_button(self):
        document, line = self._old_entry(state_edoc="autorizada")
        with self.assertRaises(UserError) as error:
            line._sped_credit("pis")
        self.assertNotIn("Recalculate Entry CST", error.exception.args[0])

    def test_the_stop_reaches_the_screen_for_a_draft_in_a_debug_declaration(self):
        """Step by step: an imported entry of use and consumption still in typing,
        with the entry CST 50 of the old rule; a declaration of the EFD
        Contribuicoes in debug mode (the only one that takes documents in typing);
        Pull Registers from Odoo. The pull reports the stop with the button. A
        declaration that is not in debug mode never takes a document in typing: the
        documents of the file are the authorized ones."""
        document, line = self._old_entry()
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_pis_cofins")
        values = {
            "company_id": self.company.id,
            "DT_INI": date(2026, 7, 1),
            "DT_FIN": date(2026, 7, 31),
        }
        normal = self.env["l10n_br_sped.efd_pis_cofins.0000"].create(values)
        self.assertNotIn(document, normal.fiscal_document_ids)
        debug = self.env["l10n_br_sped.efd_pis_cofins.0000"].create(
            {**values, "debug": True}
        )
        self.assertIn(document, debug.fiscal_document_ids)
        errors = debug._populate_sped_from_odoo()
        self.assertTrue(any("Recalculate Entry CST" in err for err in errors))
