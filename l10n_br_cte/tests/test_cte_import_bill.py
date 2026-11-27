# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.l10n_br_fiscal_edi.tests.common import EdiImportCase

from .test_cte_document_import import (
    COLLECTION,
    CTE_KEY,
    LUCRO_PRESUMIDO,
    cte_xml,
)


@tagged("post_install", "-at_install")
class TestCteImportBill(EdiImportCase):
    """The bill that "Generate invoice" makes from an imported CT-e."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.presumed = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.Document.search([("document_key", "=", CTE_KEY)]).unlink()
        cls.Document.search(
            [
                ("company_id", "=", cls.presumed.id),
                ("document_type_id.code", "=", "57"),
                ("document_number", "=", "573"),
            ]
        ).unlink()
        cls.service = cls.env["product.product"].create(
            {"name": "Freight", "type": "service"}
        )

    def _import(self, content):
        model = self.Document.with_company(self.presumed)
        if not hasattr(model, "action_generate_invoice"):
            self.skipTest("l10n_br_account_edi is not installed")
        documents, errors, _warnings = model._edi_import_files([("cte.xml", content)])
        self.assertFalse(errors)
        return documents

    def _bill(self, documents):
        documents.fiscal_line_ids.write({"product_id": self.service.id})
        documents.fiscal_line_ids.action_resolve_line()
        action = documents.action_generate_invoice()
        return self.env["account.move"].browse(action["res_id"])

    def _due(self, move):
        lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        ).sorted("date_maturity")
        return [(line.date_maturity.isoformat(), abs(line.balance)) for line in lines]

    def test_the_bill_of_a_received_cte_falls_due_as_the_file_declares(self):
        documents = self._import(cte_xml(COLLECTION))
        documents.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")
        move = self._bill(documents)
        self.assertEqual(move.move_type, "in_invoice")
        self.assertEqual(self._due(move), [("2026-12-10", 40.0), ("2027-01-10", 60.0)])

    def test_the_invoice_of_a_cte_issued_by_the_company_has_the_declared_terms(self):
        content = cte_xml(
            COLLECTION, recipient="12345678000195", emitter=LUCRO_PRESUMIDO
        )
        documents = self._import(content)
        documents.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        move = self._bill(documents)
        self.assertEqual(move.move_type, "out_invoice")
        self.assertEqual(self._due(move), [("2026-12-10", 40.0), ("2027-01-10", 60.0)])
