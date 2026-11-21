# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError

from .common import DdaCommon, make_cnpj


class TestActions(DdaCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write({"dda_auto_link": False, "dda_create_bill_mode": "draft"})
        cls.vendor = cls.make_vendor("Vendor Actions", "821137650001")
        cls.vendor_cnpj = cls.cnpj_of(cls.vendor)

    def test_link_and_undo(self):
        bill = self.make_bill(self.vendor, 700.0, self.day(5), "42")
        debit = self.upsert(self.boleto(self.vendor_cnpj, 700.0, self.day(5)))
        self.assertTrue(debit.action_apply_recommended()["linked"])
        self.assertEqual(debit.state, "linked")
        self.assertEqual(debit.link_mode, "manual")
        self.assertEqual(debit.linked_by_id, self.env.user)
        self.assertEqual(debit.recommended_action, "add_to_payment")
        self.assertTrue(debit.action_undo())
        self.assertFalse(debit.allocation_ids)
        self.assertEqual(debit.state, "suggested")
        self.assertEqual(debit.match_ids.move_line_ids, self.payable_line(bill))
        self.assertFalse(debit.action_undo())

    def test_link_checks_current_state(self):
        bill = self.make_bill(self.vendor, 710.0, self.day(5))
        debit = self.upsert(self.boleto(self.vendor_cnpj, 710.0, self.day(5)))
        debit.action_link(self.payable_line(bill).ids)
        with self.assertRaises(UserError):
            debit.action_link(self.payable_line(bill).ids)
        with self.assertRaises(UserError):
            debit.action_ignore("late")

    def test_link_many_requires_matching_sum(self):
        a = self.make_bill(self.vendor, 100.0, self.day(5))
        b = self.make_bill(self.vendor, 100.0, self.day(5))
        debit = self.upsert(self.boleto(self.vendor_cnpj, 250.0, self.day(5)))
        with self.assertRaises(UserError):
            debit.action_link((self.payable_line(a) | self.payable_line(b)).ids)

    def test_ignore_and_undo(self):
        debit = self.upsert(self.boleto(self.vendor_cnpj, 20.0, self.day(5)))
        with self.assertRaises(UserError):
            debit.action_ignore("  ")
        debit.action_ignore("Not ours")
        self.assertEqual(debit.state, "ignored")
        self.assertEqual(debit.ignore_reason, "Not ours")
        self.assertEqual(debit.recommended_action, "none")
        self.assertTrue(debit.action_undo())
        self.assertIn(debit.state, ("new", "suggested"))
        self.assertFalse(debit.ignore_reason)

    def test_create_bill_then_post_links_and_undo_before_posting(self):
        debit = self.upsert(
            self.boleto(self.vendor_cnpj, 480.0, self.day(9), document_number="B-9")
        )
        self.assertEqual(debit.recommended_action, "create_bill")
        summary = debit.action_apply_recommended()
        self.assertEqual(summary["bills"], 1)
        bill = debit.bill_id
        self.assertEqual(bill.state, "draft")
        self.assertEqual(bill.partner_id, self.vendor)
        self.assertEqual(bill.amount_total, 480.0)
        self.assertEqual(bill.invoice_date_due, self.day(9))
        self.assertTrue(debit.action_undo())
        self.assertFalse(debit.bill_id)
        self.assertFalse(bill.exists())

        debit.action_create_bill()
        bill = debit.bill_id
        bill.action_post()
        self.assertEqual(debit.state, "linked")
        self.assertEqual(debit.allocation_ids.move_line_id.move_id, bill)
        # Posted bills are not touched by undo.
        self.assertFalse(debit.action_undo())
        self.assertEqual(bill.state, "posted")

    def test_create_bill_needs_a_vendor(self):
        debit = self.upsert(self.boleto(make_cnpj("859507830001"), 30.0, self.day(9)))
        with self.assertRaises(UserError):
            debit.action_create_bill()

    def test_due_date_update_is_explicit_and_reversible(self):
        bill = self.make_bill(self.vendor, 90.0, self.day(5))
        debit = self.upsert(self.boleto(self.vendor_cnpj, 90.0, self.day(7)))
        line = self.payable_line(bill)
        debit.action_link(line.ids, update_due=True)
        self.assertEqual(line.date_maturity, self.day(7))
        debit.action_undo()
        self.assertEqual(line.date_maturity, self.day(5))

    def test_verify_needs_approver(self):
        debit = self.upsert(self.boleto(make_cnpj("796349180001"), 31.0, self.day(9)))
        user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "DDA plain user",
                    "login": "dda_plain_user",
                    "company_id": self.company.id,
                    "company_ids": [(6, 0, self.company.ids)],
                    "groups_id": [
                        (6, 0, [self.env.ref("l10n_br_dda.group_dda_user").id])
                    ],
                }
            )
        )
        with self.assertRaises(AccessError):
            debit.with_user(user).action_mark_verified()

    def test_undo_verification_restores_suspect(self):
        debit = self.upsert(self.boleto(make_cnpj("721671870001"), 32.0, self.day(9)))
        debit.action_mark_verified()
        self.assertEqual(debit.state, "new")
        self.assertTrue(debit.action_undo())
        self.assertEqual(debit.state, "suspect")

    def test_batch_summary_counts_skipped(self):
        bill = self.make_bill(self.vendor, 55.0, self.day(5))
        good = self.upsert(self.boleto(self.vendor_cnpj, 55.0, self.day(5)))
        review = self.upsert(self.boleto(make_cnpj("768031010001"), 56.0, self.day(5)))
        summary = (good | review).action_apply_recommended()
        self.assertEqual(summary["linked"], 1)
        self.assertEqual(summary["skipped"], 1)
        self.assertEqual(summary["total_amount"], 55.0)
        self.assertEqual(good.allocation_ids.move_line_id, self.payable_line(bill))

    def test_match_wizard_links_selected_candidate(self):
        bill = self.make_bill(self.vendor, 77.0, self.day(5))
        debit = self.upsert(self.boleto(self.vendor_cnpj, 77.0, self.day(6)))
        action = debit.action_open_match_wizard()
        wizard = self.env["l10n_br_dda.match.wizard"].browse(action["res_id"])
        self.assertEqual(len(wizard.candidate_ids), 1)
        wizard.candidate_ids.selected = True
        wizard.due_policy = "update"
        wizard.action_confirm()
        self.assertEqual(debit.state, "linked")
        self.assertEqual(self.payable_line(bill).date_maturity, self.day(6))

    def test_ignore_wizard_in_batch(self):
        one = self.upsert(self.boleto(self.vendor_cnpj, 11.0, self.day(5)))
        two = self.upsert(self.boleto(self.vendor_cnpj, 12.0, self.day(5)))
        wizard = self.env["l10n_br_dda.ignore.wizard"].create(
            {"debit_ids": [(6, 0, (one | two).ids)], "reason": "Test"}
        )
        wizard.action_confirm()
        self.assertEqual((one | two).mapped("state"), ["ignored", "ignored"])

    def test_dashboard(self):
        self.make_bill(self.vendor, 15.0, self.day(2))
        self.upsert(
            self.boleto(self.vendor_cnpj, 15.0, self.day(2)),
            self.boleto(make_cnpj("894416570001"), 16.0, self.day(-3)),
        )
        data = self.env["l10n_br_dda.debit"].dda_dashboard()
        self.assertEqual(
            sorted(data["counters"]),
            ["divergence", "due_7", "new", "overdue", "suspect"],
        )
        self.assertEqual(sorted(data["domains"]), sorted(data["counters"]))
        self.assertGreaterEqual(data["counters"]["suspect"], 1)
        self.assertGreaterEqual(data["counters"]["overdue"], 1)
        self.assertIn("symbol", data["currency"])
        self.assertIsInstance(data["sources"], list)
        overdue = self.env["l10n_br_dda.debit"].search(data["domains"]["overdue"])
        self.assertTrue(overdue)

    def test_expire_cron(self):
        debit = self.upsert(
            self.boleto(self.vendor_cnpj, 14.0, self.day(-40), date_limit=self.day(-1))
        )
        self.env["l10n_br_dda.debit"]._cron_dda_expire()
        self.assertEqual(debit.state, "expired")
