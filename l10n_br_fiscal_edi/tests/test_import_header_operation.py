# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date
from unittest.mock import patch

from odoo.tests import Form, tagged

from ..tools import EdiInstallment
from .common import EdiImportCase


@tagged("post_install", "-at_install")
class TestImportHeaderOperation(EdiImportCase):
    """The operation chosen on the header of an imported document reaches its lines,
    and what the file declared is not touched by it."""

    def _declared_document(self, code="55", issuer="partner"):
        document_type = self.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", code)], limit=1
        )
        document = self._create_imported_document(
            document_type_id=document_type.id,
            issuer=issuer,
            document_serie="1",
            # a number the demo documents of other modules do not use: a document
            # of the company cannot repeat the serie and the number of another one
            document_number="999001",
            fiscal_operation_id=False,
            lines=[{"name": "Freight", "price_unit": 100.0}],
        )
        document._init_import_states()
        return document

    def _declare_installments(self):
        installments = [
            EdiInstallment("001", date(2026, 12, 10), 60.0),
            EdiInstallment("002", date(2027, 1, 10), 40.0),
        ]
        patcher = patch.object(
            type(self.Document), "_edi_get_installments", lambda doc: installments
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _choose_operation(self, document, operation):
        with Form(document) as form:
            form.fiscal_operation_id = operation
        return document

    def _declared(self, document):
        line = document.fiscal_line_ids
        return {
            "price_unit": line.price_unit,
            "quantity": line.quantity,
            "fiscal_amount_total": line.fiscal_amount_total,
        }

    def test_the_operation_of_the_header_reaches_the_lines(self):
        document = self._declared_document()
        line = document.fiscal_line_ids
        self.assertFalse(line.fiscal_operation_id)
        operation = self.env.ref("l10n_br_fiscal.fo_compras")
        self._choose_operation(document, operation)
        self.assertEqual(line.fiscal_operation_id, operation)
        self.assertTrue(line.fiscal_operation_line_id)

    def test_what_the_file_declared_is_not_touched_by_the_operation(self):
        document = self._declared_document()
        before = self._declared(document)
        self.assertEqual(before["price_unit"], 100.0)
        self._choose_operation(document, self.env.ref("l10n_br_fiscal.fo_compras"))
        self.assertEqual(self._declared(document), before)

    def test_the_amounts_of_the_document_stay_the_ones_of_the_file(self):
        document = self._declared_document()
        self._choose_operation(document, self.env.ref("l10n_br_fiscal.fo_compras"))
        self.assertAlmostEqual(document.fiscal_amount_total, 100.0)
        self.assertAlmostEqual(document.amount_financial_total, 100.0)
        gross, withholding, net = document._edi_payment_totals()
        self.assertEqual((gross, withholding, net), (100.0, 0.0, 100.0))

    def test_the_page_of_installments_warns_of_nothing_with_the_operation(self):
        document = self._declared_document()
        self._declare_installments()
        self._choose_operation(document, self.env.ref("l10n_br_fiscal.fo_compras"))
        self.assertFalse(document._edi_installment_warning())

    def test_a_line_that_has_an_operation_keeps_it(self):
        document = self._declared_document()
        other = self.env.ref("l10n_br_fiscal.fo_venda")
        line = document.fiscal_line_ids
        line.fiscal_operation_id = other
        self._choose_operation(document, self.env.ref("l10n_br_fiscal.fo_compras"))
        self.assertEqual(line.fiscal_operation_id, other)

    def test_a_document_the_company_issued_keeps_its_amounts_when_confirmed(self):
        document = self._declared_document(issuer="company")
        operation = self.env.ref("l10n_br_fiscal.fo_venda")
        self._choose_operation(document, operation)
        line = document.fiscal_line_ids
        self.assertEqual(line.fiscal_operation_id, operation)
        self.assertTrue(line.fiscal_operation_line_id)
        self.assertAlmostEqual(document.amount_financial_total, 100.0)
        line._apply_import_depara(
            product=self.env["product.product"].create({"name": "Own item"}),
            uom=self.uom_unit,
        )
        self.assertAlmostEqual(document.amount_financial_total, 100.0)
        document.action_document_confirm()
        self.assertEqual(document.state_edoc, "autorizada")
        self.assertAlmostEqual(document.amount_financial_total, 100.0)
        self.assertAlmostEqual(document.fiscal_amount_total, 100.0)

    def _unmatched_document(self):
        """A document whose line has a CFOP that no operation line answers (a CT-e)
        and no product to pick one."""
        document = self._declared_document()
        cfop = self.env["l10n_br_fiscal.cfop"].search([("code", "=", "5352")], limit=1)
        self.assertTrue(cfop)
        document.fiscal_line_ids.partner_cfop_id = cfop
        return document

    def _operation(self, lines):
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": f"TST-{lines}",
                "name": f"Test operation with {lines} line(s)",
                "fiscal_operation_type": "in",
                "fiscal_type": "purchase",
            }
        )
        for number in range(lines):
            self.env["l10n_br_fiscal.operation.line"].create(
                {
                    "fiscal_operation_id": operation.id,
                    "name": f"Line {number}",
                    "cfop_internal_id": self.env.ref("l10n_br_fiscal.cfop_1102").id,
                    # the line has no product, so the definition by product picks none
                    "product_type": "00",
                }
            )
        operation.action_approve()
        return operation

    def test_a_single_candidate_line_is_applied_when_no_cfop_matches(self):
        """The operation has one approved line: it is the one, so the line adds to
        the total as the amounts of the file."""
        document = self._unmatched_document()
        operation = self._operation(1)
        self._choose_operation(document, operation)
        line = document.fiscal_line_ids
        self.assertEqual(line.fiscal_operation_line_id, operation.line_ids)
        self.assertAlmostEqual(document.amount_financial_total, 100.0)
        self.assertNotIn("operation line", document.import_warning or "")

    def test_several_candidate_lines_are_left_to_the_person_with_a_warning(self):
        """With more than one candidate nothing is guessed: the line stays without
        operation line and the document tells the person to choose."""
        document = self._unmatched_document()
        operation = self._operation(2)
        self._choose_operation(document, operation)
        line = document.fiscal_line_ids
        self.assertFalse(line.fiscal_operation_line_id)
        self.assertIn("choose the operation line", document.import_warning)
        line.fiscal_operation_line_id = operation.line_ids[:1]
        self.assertNotIn("choose the operation line", document.import_warning or "")

    def test_a_line_of_another_operation_that_answers_the_cfop_is_not_taken(self):
        """Another operation has a line for the CFOP of the file, but the person
        chose a different operation: the line stays with the chosen one and waits for
        its operation line."""
        other = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": "TST-OTHER",
                "name": "Another test operation",
                "fiscal_operation_type": "in",
                "fiscal_type": "purchase",
            }
        )
        self.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": other.id,
                "name": "Answers the CFOP of the file",
                "cfop_internal_id": self.env.ref("l10n_br_fiscal.cfop_1352").id,
                "product_type": "00",
            }
        )
        other.action_approve()
        document = self._unmatched_document()
        operation = self._operation(2)
        self._choose_operation(document, operation)
        line = document.fiscal_line_ids
        self.assertEqual(line.fiscal_operation_id, operation)
        self.assertFalse(line.fiscal_operation_line_id)
        self.assertIn("choose the operation line", document.import_warning)

    def test_a_document_without_amount_to_pay_shows_why(self):
        """The type of the document can say that it is only registered: the reason
        is a warning of the document and goes away with it."""
        document = self._declared_document()
        self.assertFalse(document._edi_no_payable_reason())
        self.assertNotIn("Registered only", document.import_warning or "")
        with patch.object(
            type(document),
            "_edi_no_payable_reason",
            lambda doc: "Registered only, with no amount to pay.",
        ):
            document.invalidate_recordset(["import_warning"])
            self.assertIn("Registered only", document.import_warning)
        document.invalidate_recordset(["import_warning"])
        self.assertNotIn("Registered only", document.import_warning or "")
