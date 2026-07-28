# @ 2020 KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
)


class TestSubsequentOperation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source_document = cls.env.ref(
            "l10n_br_fiscal.demo_nfe_so_simples_faturamento"
        ).copy()
        cls.so_simples_faturamento = cls.env.ref(
            "l10n_br_fiscal_subsequent_document.so_simples_faturamento"
        )
        cls.fo_entrega_futura = cls.env.ref("l10n_br_fiscal.fo_entrega_futura")

    def _expected_tax(self, operation_line, tax_group):
        tax_definition = operation_line.tax_definition_ids.filtered(
            lambda d: d.tax_group_id == tax_group and d.state == "approved"
        )
        return tax_definition.tax_id

    def test_populate_subsequent_from_operation(self):
        """Operation config must populate the document subsequent lines."""
        subsequent = self.source_document.document_subsequent_ids
        self.assertTrue(
            subsequent,
            "Document of an operation with subsequent config has no "
            "subsequent lines",
        )
        self.assertEqual(
            subsequent.subsequent_operation_id, self.so_simples_faturamento
        )
        self.assertEqual(subsequent.fiscal_operation_id, self.fo_entrega_futura)
        self.assertFalse(subsequent.operation_performed)
        self.assertFalse(self.source_document.document_subsequent_generated)

        # Changing to an operation without subsequent config rebuilds the lines
        self.source_document.fiscal_operation_id = self.env.ref(
            "l10n_br_fiscal.fo_venda"
        )
        self.assertFalse(self.source_document.document_subsequent_ids)

    def test_subsequent_operation_simple_faturamento(self):
        """Confirming the source document generates the subsequent one."""
        self.source_document.action_document_confirm()
        self.assertEqual(self.source_document.state_edoc, SITUACAO_EDOC_A_ENVIAR)

        subsequent = self.source_document.document_subsequent_ids
        generated = subsequent.subsequent_document_id
        self.assertTrue(generated, "Subsequent document was not created")
        self.assertTrue(subsequent.operation_performed)
        self.assertTrue(self.source_document.document_subsequent_generated)

        # Generated document carries the subsequent operation, remapped lines
        self.assertEqual(generated.fiscal_operation_id, self.fo_entrega_futura)
        for line in generated.fiscal_line_ids:
            self.assertEqual(
                line.fiscal_operation_line_id.fiscal_operation_id,
                self.fo_entrega_futura,
                "Line was not remapped to the subsequent operation",
            )
            self.assertEqual(
                line.cfop_id,
                line.fiscal_operation_line_id.cfop_internal_id,
                "CFOP was not remapped to the subsequent operation line",
            )
            for group_ref, tax_field in [
                ("l10n_br_fiscal.tax_group_pis", "pis_tax_id"),
                ("l10n_br_fiscal.tax_group_cofins", "cofins_tax_id"),
            ]:
                expected_tax = self._expected_tax(
                    line.fiscal_operation_line_id, self.env.ref(group_ref)
                )
                if expected_tax:
                    self.assertEqual(line[tax_field], expected_tax)

        # The generated document references the source one
        self.assertIn(
            self.source_document,
            generated.document_related_ids.mapped("document_related_id"),
            "Generated document does not reference the source document",
        )

        # The generated document must not inherit the subsequent config
        # of the source operation (no chained regeneration)
        self.assertFalse(generated.document_subsequent_ids)

        # Generation is idempotent
        self.assertEqual(subsequent._generate_subsequent_document(), generated)

        # A performed subsequent line cannot be deleted
        with self.assertRaises(UserError):
            subsequent.unlink()

    def test_cancel_guard(self):
        """Source cannot be cancelled once the subsequent doc is authorized."""
        self.source_document.action_document_confirm()
        generated = self.source_document.document_subsequent_ids.subsequent_document_id
        generated._change_state(SITUACAO_EDOC_AUTORIZADA)
        with self.assertRaises(UserError):
            self.source_document._document_cancel("cancel test")
