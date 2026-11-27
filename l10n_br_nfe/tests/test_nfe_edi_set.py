# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal_edi.tools import EdiInstallment, EdiPayment


class TestNFeEdiSet(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document = cls.env.ref("l10n_br_nfe.demo_nfe_same_state")
        cls.today = fields.Date.context_today(cls.document)

    def _installments(self, *days):
        total = self.document.amount_financial_total
        return [
            EdiInstallment(
                number=str(index).zfill(3),
                date_due=self.today + timedelta(days=day),
                amount=total / len(days),
            )
            for index, day in enumerate(days, 1)
        ]

    def _payment(self, means="15", term="installments", amount=None):
        return EdiPayment(
            means=means,
            amount=self.document.amount_financial_total if amount is None else amount,
            term=term,
        )

    def test_duplicates_are_written_when_the_payment_is_on_terms(self):
        self.assertTrue(self.document.amount_financial_total)
        self.assertFalse(self.document.nfe40_dup)
        self.document._edi_set_installments(self._installments(30, 60))
        self.assertEqual(self.document.nfe40_dup.mapped("nfe40_nDup"), ["001", "002"])
        self.assertEqual(
            self.document.nfe40_dup.mapped("nfe40_dVenc"),
            [self.today + timedelta(days=30), self.today + timedelta(days=60)],
        )

    def test_duplicates_are_replaced_not_accumulated(self):
        self.document._edi_set_installments(self._installments(30, 60))
        self.document._edi_set_installments(self._installments(15))
        self.assertEqual(self.document.nfe40_dup.mapped("nfe40_nDup"), ["001"])

    def test_no_duplicate_when_everything_is_due_on_the_issue_date(self):
        self.document._edi_set_installments(self._installments(0))
        self.assertFalse(self.document.nfe40_dup)

    def test_no_duplicate_on_nfce(self):
        nfce = self.env.ref("l10n_br_nfe.demo_nfce_same_state")
        nfce._edi_set_installments(self._installments(30))
        self.assertFalse(nfce.nfe40_dup)

    def test_payment_on_terms(self):
        self.document._edi_set_payments([self._payment()])
        payment = self.document.nfe40_detPag
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.nfe40_indPag, "1")
        self.assertEqual(payment.nfe40_tPag, "15")
        self.assertEqual(payment.nfe40_vPag, self.document.amount_financial_total)

    def test_payment_in_cash_and_without_a_means_of_payment(self):
        self.document._edi_set_payments([self._payment(means="", term="cash")])
        payment = self.document.nfe40_detPag
        self.assertEqual((payment.nfe40_indPag, payment.nfe40_tPag), ("0", ""))

    def test_payment_is_replaced_not_accumulated(self):
        self.document._edi_set_payments([self._payment()])
        self.document._edi_set_payments([self._payment(means="17", term="cash")])
        self.assertEqual(self.document.nfe40_detPag.mapped("nfe40_tPag"), ["17"])

    def test_no_payment_means_not_paid(self):
        self.document._edi_set_payments([self._payment(means="90")])
        payment = self.document.nfe40_detPag
        self.assertEqual(
            (payment.nfe40_indPag, payment.nfe40_tPag, payment.nfe40_vPag),
            ("0", "90", 0.0),
        )

    def test_devolution_and_adjustment_declare_no_payment(self):
        for purpose in ("4", "3"):
            self.document.edoc_purpose = purpose
            self.document._edi_set_payments([self._payment()])
            payment = self.document.nfe40_detPag
            self.assertEqual((payment.nfe40_tPag, payment.nfe40_vPag), ("90", 0.0))

    def test_document_of_a_supplier_is_left_alone(self):
        self.document.issuer = "partner"
        self.document._edi_set_installments(self._installments(30))
        self.document._edi_set_payments([self._payment()])
        self.assertFalse(self.document.nfe40_dup)
        self.assertFalse(self.document.nfe40_detPag)
