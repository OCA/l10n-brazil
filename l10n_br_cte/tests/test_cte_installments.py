# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import SkipTest
from unittest.mock import patch

from odoo import Command
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCteInstallments(TransactionCase):
    """The collection (cobr) of a CT-e that the company issues from an invoice."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group = cls.env.ref(
            "l10n_br_account.group_line_fiscal_detail", raise_if_not_found=False
        )
        if not group:
            raise SkipTest("l10n_br_account is not installed")
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        companies = cls.env["res.company"].search([])
        cls.env.user.company_ids = [Command.set(companies.ids)]
        cls.env.user.company_id = cls.company
        cls.env.user.groups_id |= group
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                allowed_company_ids=companies.ids,
            )
        )
        cls.two_terms = cls.env["account.payment.term"].create(
            {
                "name": "2x",
                "line_ids": [
                    (0, 0, {"value": "percent", "value_amount": 50, "days": 30}),
                    (0, 0, {"value": "balance", "days": 60}),
                ],
            }
        )
        cls.in_cash = cls.env["account.payment.term"].create(
            {"name": "cash", "line_ids": [(0, 0, {"value": "balance", "days": 0})]}
        )

    def _invoice(self, term=None, price=100.0, cte_type=None):
        form = Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        )
        form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        form.document_type_id = self.env.ref("l10n_br_fiscal.document_57")
        form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        form.invoice_payment_term_id = term or self.two_terms
        with form.invoice_line_ids.new() as line:
            line.product_id = self.env.ref("product.product_product_7")
            line.price_unit = price
        move = form.save()
        if cte_type:
            move.fiscal_document_id.cte40_tpCTe = cte_type
        return move

    def _post(self, move):
        """Post the invoice. The XML of the CT-e is exported at the posting too, and
        the invoice made in the test has none of the ICMS and modal data that the
        export asks for: the serialization is the object of its own test."""
        with patch.object(type(move.fiscal_document_id), "_document_export"):
            move._post()

    def test_the_installments_are_previewed_before_and_written_at_posting(self):
        move = self._invoice()
        document = move.fiscal_document_id
        self.assertFalse(document.cte40_cobr)
        for summary in (move.edi_payment_summary, document.edi_payment_summary):
            self.assertIn("001", str(summary))
            self.assertIn("002", str(summary))
        self._post(move)
        collection = document.cte40_cobr
        self.assertEqual(collection.cte40_dup.mapped("cte40_nDup"), ["001", "002"])
        self.assertEqual(collection.cte40_dup.mapped("cte40_vDup"), [50.0, 50.0])
        self.assertEqual(
            collection.cte40_dup.mapped("cte40_dVenc"),
            [line.date_due for line in move._edi_installments()],
        )
        self.assertEqual(collection.cte40_fat.cte40_vOrig, 100.0)
        self.assertEqual(collection.cte40_fat.cte40_vLiq, 100.0)
        self.assertFalse(collection.cte40_fat.cte40_vDesc)

    def test_what_is_paid_in_cash_has_no_collection(self):
        move = self._invoice(term=self.in_cash)
        self._post(move)
        self.assertFalse(move.fiscal_document_id.cte40_cobr)

    def test_the_complement_has_no_collection(self):
        """The layout has the collection in the normal and the substitute CT-e only
        (the annulment is not issued from an invoice)."""
        move = self._invoice(cte_type="1")
        self._post(move)
        self.assertFalse(move.fiscal_document_id.cte40_cobr)

    def test_the_substitute_cte_has_a_collection(self):
        move = self._invoice(cte_type="3")
        self._post(move)
        self.assertEqual(len(move.fiscal_document_id.cte40_cobr.cte40_dup), 2)

    def test_a_document_imported_as_issued_by_the_company_is_never_rewritten(self):
        move = self._invoice()
        document = move.fiscal_document_id
        document.imported_document = True
        document._edi_set_installments(move._edi_installments())
        self.assertFalse(document.cte40_cobr)

    def test_another_type_of_document_is_left_as_it_is(self):
        move = self._invoice()
        document = move.fiscal_document_id
        document.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        document._edi_set_installments(move._edi_installments())
        self.assertFalse(document.cte40_cobr)

    def test_posting_again_does_not_duplicate_the_duplicates(self):
        move = self._invoice()
        document = move.fiscal_document_id
        document._edi_set_installments(move._edi_installments())
        # the demo data of the module has collections of its own: what counts is
        # that writing again creates nothing
        cobr_model = self.env["cte.40.tcte_cobr"]
        fat_model = self.env["cte.40.tcte_fat"]
        counts = (cobr_model.search_count([]), fat_model.search_count([]))
        document._edi_set_installments(move._edi_installments())
        self.assertEqual(len(document.cte40_cobr.cte40_dup), 2)
        self.assertEqual(len(document.cte40_cobr), 1)
        self.assertEqual(
            (cobr_model.search_count([]), fat_model.search_count([])), counts
        )

    def test_the_invoice_of_the_collection_takes_the_number_of_the_cte(self):
        move = self._invoice()
        self._post(move)
        document = move.fiscal_document_id
        self.assertTrue(document.document_number)
        self.assertEqual(
            document.cte40_cobr.cte40_fat.cte40_nFat, document.document_number
        )
