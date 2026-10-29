# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_dda.constants import STATUS_CANCELLED
from odoo.addons.l10n_br_dda.tests.common import DdaCommon
from odoo.addons.l10n_br_dda.utils import build_digitable_line


class TestDdaPaymentSchedule(DdaCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.dda_auto_link = False
        cls.vendor = cls.make_vendor("Vendor A", "862407430001")
        cls.mode = cls.env["account.payment.mode"].create(
            {
                "name": "Boleto",
                "company_id": cls.company.id,
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.company_data["default_journal_bank"].id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_out"
                ).id,
                "payment_mode_domain": "boleto",
            }
        )

    def _item(self, amount, number):
        bill = self.make_bill(self.vendor, amount, self.day(5), number)
        line = self.payable_line(bill)
        line.payment_mode_id = self.mode
        return line

    def _debit(self, amount, seed):
        line = build_digitable_line("001", amount, self.day(5), seed)
        return self.upsert(
            self.boleto(
                self.cnpj_of(self.vendor), amount, self.day(5), digitable_line=line
            )
        )

    def test_linked_boleto_is_the_instrument_until_cancelled(self):
        line = self._item(1000.0, "101")
        debit = self._debit(1000.0, "a")
        self.assertEqual(line.payment_schedule_state, "missing_instrument")
        debit.action_link(line.ids)
        self.assertEqual(line.dda_debit_id, debit)
        self.assertEqual(line.payment_digitable_line, debit.digitable_line)
        self.assertEqual(debit.allocation_ids.payment_schedule_state, "to_schedule")
        self.assertFalse(debit.payment_schedule_warning)
        debit._dda_apply_status(STATUS_CANCELLED)
        self.assertFalse(line.dda_debit_id)
        self.assertFalse(line.payment_barcode)
        self.assertEqual(line.payment_schedule_state, "missing_instrument")

    def test_other_barcode_is_kept_and_flagged(self):
        line = self._item(500.0, "202")
        line.payment_barcode = build_digitable_line("001", 500.0, self.day(5), "own")
        own = line.payment_barcode
        debit = self._debit(510.0, "b")
        debit.action_link(line.ids)
        self.assertEqual(line.payment_barcode, own)
        self.assertTrue(line.dda_barcode_divergent)
        self.assertIn("another barcode", debit.payment_schedule_warning)
        self.assertIn("differs from the open amount", debit.payment_schedule_warning)
        debit.action_undo()
        self.assertEqual(line.payment_barcode, own)
        self.assertFalse(line.dda_debit_id)

    def test_installments_take_the_barcode_on_the_first_one(self):
        first = self._item(600.0, "7007")
        second = self._item(400.0, "7008")
        debit = self._debit(1000.0, "c")
        debit.action_link((first | second).ids)
        self.assertEqual((first | second).dda_debit_id, debit)
        self.assertEqual(first.payment_digitable_line, debit.digitable_line)
        self.assertFalse(second.payment_barcode)
        self.assertFalse(debit.payment_schedule_warning)
