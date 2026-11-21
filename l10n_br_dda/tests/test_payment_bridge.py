# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import DdaCommon, make_cnpj


class TestPaymentBridge(DdaCommon):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.vendor = cls.make_vendor("Vendor Bridge", "628397580001")
        cls.vendor_cnpj = cls.cnpj_of(cls.vendor)
        cls.mode = cls.env["account.payment.mode"].create(
            {
                "name": "DDA TED",
                "company_id": cls.company.id,
                "bank_account_link": "variable",
                "payment_method_id": cls.env.ref(
                    "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
                ).id,
                "payment_mode_domain": "ted",
                "payment_order_ok": True,
                "variable_journal_ids": [
                    (6, 0, cls.company_data["default_journal_bank"].ids)
                ],
            }
        )
        cls.company.dda_payment_mode_id = cls.mode

    def _linked_debit(self, amount, due, number, **extra):
        bill = self.make_bill(self.vendor, 3500.0, due, number)
        debit = self.upsert(
            self.boleto(self.vendor_cnpj, amount, due, document_number=number, **extra)
        )
        debit.action_link(self.payable_line(bill).ids)
        return bill, debit

    def test_payment_line_gets_boleto_data(self):
        bill, debit = self._linked_debit(
            3500.0,
            self.day(10),
            "2002",
            barcode="34191" + "1" * 39,
            interest_amount=87.5,
            fine_amount=25.0,
            discount_amount=10.0,
        )
        debit.action_add_to_payment_order()
        self.assertEqual(debit.state, "in_payment")
        order = debit.payment_order_id
        self.assertEqual(order.state, "draft")
        self.assertEqual(order.payment_mode_id, self.mode)
        payline = order.payment_line_ids
        self.assertEqual(len(payline), 1)
        self.assertEqual(payline.move_line_id, self.payable_line(bill))
        self.assertEqual(payline.digitable_line, debit.digitable_line)
        self.assertEqual(payline.barcode, "34191" + "1" * 39)
        self.assertEqual(payline.interest_value, 87.5)
        self.assertEqual(payline.fee_value, 25.0)
        self.assertEqual(payline.discount_value, 10.0)
        self.assertEqual(payline.amount_currency, 3500.0)
        self.assertEqual(self.payable_line(bill).cnab_state, "added")
        self.assertEqual(debit.recommended_action, "none")
        with self.assertRaises(UserError):
            debit.action_add_to_payment_order()

    def test_nominal_difference_goes_to_the_write_off(self):
        bill, debit = self._linked_debit(3612.5, self.day(10), "2003")
        debit.action_add_to_payment_order()
        payline = debit.payment_order_id.payment_line_ids
        self.assertEqual(payline.interest_value, 112.5)
        self.assertEqual(payline.discount_value, 0.0)
        self.assertEqual(bill.amount_total, 3500.0)

    def test_undo_removes_the_payment_line(self):
        bill, debit = self._linked_debit(3500.0, self.day(10), "2004")
        debit.action_add_to_payment_order()
        order = debit.payment_order_id
        self.assertTrue(debit.action_undo())
        self.assertEqual(debit.state, "linked")
        self.assertFalse(debit.payment_order_id)
        self.assertFalse(order.exists())
        self.assertEqual(self.payable_line(bill).cnab_state, "draft")

    def test_undo_is_refused_when_the_order_is_not_draft(self):
        bill, debit = self._linked_debit(3500.0, self.day(10), "2005")
        debit.action_add_to_payment_order()
        debit.payment_order_id.write({"state": "open"})
        self.assertFalse(debit.action_undo())
        self.assertEqual(debit.state, "in_payment")

    def test_line_in_order_is_not_offered_to_another_boleto(self):
        bill, debit = self._linked_debit(3500.0, self.day(10), "2006")
        debit.action_add_to_payment_order()
        other = self.upsert(self.boleto(self.vendor_cnpj, 3500.0, self.day(10)))
        self.assertFalse(other.match_ids)

    def test_suspect_boleto_cannot_enter_an_order(self):
        bill = self.make_bill(self.vendor, 40.0, self.day(5))
        debit = self.upsert(self.boleto(make_cnpj("704894680001"), 40.0, self.day(5)))
        self.assertEqual(debit.state, "suspect")
        debit.action_link(self.payable_line(bill).ids)
        self.assertTrue(debit.is_suspect)
        with self.assertRaises(UserError):
            debit.action_add_to_payment_order()
        debit.action_mark_verified()
        debit.action_add_to_payment_order()
        self.assertEqual(debit.state, "in_payment")

    def test_missing_payment_mode_is_explained(self):
        self.company.dda_payment_mode_id = False
        bill, debit = self._linked_debit(3500.0, self.day(10), "2007")
        with self.assertRaises(UserError):
            debit.action_add_to_payment_order()

    def test_reconciling_the_title_marks_the_boleto_paid(self):
        bill, debit = self._linked_debit(3500.0, self.day(10), "2008")
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=bill.ids
        ).create({}).action_create_payments()
        self.assertTrue(self.payable_line(bill).reconciled)
        self.assertEqual(debit.state, "paid")

    def test_installments_are_paid_once_for_the_boleto_amount(self):
        first = self.payable_line(self.make_bill(self.vendor, 600.0, self.day(10)))
        second = self.payable_line(self.make_bill(self.vendor, 400.0, self.day(10)))
        debit = self.upsert(self.boleto(self.vendor_cnpj, 1000.0, self.day(10)))
        debit.action_link((first | second).ids)
        debit.action_add_to_payment_order()
        order = debit.payment_order_id
        self.assertEqual(order.payment_line_ids.move_line_id, first)
        self.assertEqual(order.payment_line_ids.amount_currency, 1000.0)
        with self.assertRaises(UserError):
            second.create_payment_line_from_move_line(order)
        payment = self.env["account.payment"].create(
            {
                "payment_type": "outbound",
                "partner_type": "supplier",
                "partner_id": self.vendor.id,
                "amount": 1000.0,
                "journal_id": self.company_data["default_journal_bank"].id,
            }
        )
        payment.action_post()
        paid = payment.move_id.line_ids.filtered(
            lambda ln: ln.account_id == first.account_id
        )
        (paid | first).reconcile()
        self.assertTrue(first.reconciled and second.reconciled)
        self.assertEqual(debit.state, "paid")
