# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import DdaCommon, make_cnpj


class TestMatching(DdaCommon):
    """Matching by table: one row per case of the PRD."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.company.write({"dda_auto_link": False, "dda_date_tolerance": 3})
        cls.vendor = cls.make_vendor("Vendor A", "862407430001")
        cls.vendor_cnpj = cls.cnpj_of(cls.vendor)

    def test_strict_match_is_recommended_but_not_linked_when_policy_off(self):
        bill = self.make_bill(self.vendor, 1000.0, self.day(5), "1234")
        debit = self.upsert(
            self.boleto(self.vendor_cnpj, 1000.0, self.day(5), document_number="1234/1")
        )
        self.assertEqual(debit.state, "suggested")
        self.assertEqual(debit.recommended_action, "link")
        self.assertEqual(debit.recommended_move_line_id, self.payable_line(bill))
        match = debit.match_ids
        self.assertTrue(match.is_strict)
        self.assertEqual(match.score, 40 + 30 + 20 + 10)
        self.assertIn("Same document number", match.evidence)
        self.assertEqual(debit.partner_id, self.vendor)
        self.assertEqual(debit.divergence_amount, 0.0)

    def test_strict_match_links_by_itself_when_policy_on(self):
        self.company.dda_auto_link = True
        bill = self.make_bill(self.vendor, 1010.0, self.day(6), "5555")
        debit = self.upsert(
            self.boleto(self.vendor_cnpj, 1010.0, self.day(6), document_number="5555")
        )
        self.assertEqual(debit.state, "linked")
        self.assertEqual(debit.link_mode, "auto")
        self.assertFalse(debit.linked_by_id)
        self.assertEqual(debit.allocation_ids.move_line_id, self.payable_line(bill))
        self.assertIn("automatic rule", " ".join(debit.message_ids.mapped("body")))

    def test_two_equal_installments_never_link_by_themselves(self):
        self.company.dda_auto_link = True
        self.make_bill(self.vendor, 800.0, self.day(10), "9000/1")
        self.make_bill(self.vendor, 800.0, self.day(10), "9000/2")
        debit = self.upsert(
            self.boleto(self.vendor_cnpj, 800.0, self.day(10), document_number="9000/1")
        )
        self.assertEqual(debit.state, "suggested")
        self.assertEqual(len(debit.match_ids), 2)
        self.assertEqual(len(debit.match_ids.filtered("is_strict")), 2)
        self.assertEqual(debit.recommended_action, "review")

    def test_assignment_is_suggested_never_strict(self):
        self.company.dda_auto_link = True
        bill = self.make_bill(self.vendor, 500.0, self.day(8), "777")
        debit = self.upsert(
            self.boleto(
                make_cnpj("893208940001"),
                500.0,
                self.day(8),
                document_number="777",
                guarantor_vat=self.vendor_cnpj,
                guarantor_name="Vendor A",
            )
        )
        self.assertEqual(debit.state, "suggested")
        match = debit.match_ids
        self.assertEqual(match.identity_kind, "assignment")
        self.assertFalse(match.is_strict)
        self.assertEqual(match.move_line_ids, self.payable_line(bill))
        self.assertEqual(match.score, 25 + 30 + 20 + 10)
        self.assertIn("assignment", debit.alert_codes)
        self.assertEqual(debit.partner_id, self.vendor)
        self.assertEqual(debit.recommended_action, "review")

    def test_registered_assignee_is_suggested(self):
        assignee = self.make_vendor("Securitizadora", "742140830001")
        self.vendor.dda_assignee_ids = assignee
        bill = self.make_bill(self.vendor, 420.0, self.day(8))
        debit = self.upsert(self.boleto(self.cnpj_of(assignee), 420.0, self.day(8)))
        self.assertEqual(debit.match_ids.move_line_ids, self.payable_line(bill))
        self.assertEqual(debit.match_ids.identity_kind, "assignment")
        # the bank sends no guarantor: the registered assignee alone raises the alert
        self.assertTrue(debit.alert_assignment)

    def test_root_cnpj_is_suggestion_only(self):
        other_branch = make_cnpj(self.vendor_cnpj[:8] + "0002")
        self.make_bill(self.vendor, 610.0, self.day(8))
        debit = self.upsert(self.boleto(other_branch, 610.0, self.day(8)))
        self.assertEqual(debit.match_ids.identity_kind, "root")
        self.assertFalse(debit.match_ids.is_strict)
        self.assertIn("unknown_partner", debit.alert_codes)

    def test_n_to_one_installments(self):
        self.company.dda_auto_link = True
        a = self.make_bill(self.vendor, 600.0, self.day(12), "7007")
        b = self.make_bill(self.vendor, 400.0, self.day(12), "7008")
        debit = self.upsert(self.boleto(self.vendor_cnpj, 1000.0, self.day(12)))
        self.assertEqual(debit.state, "suggested")
        match = debit.match_ids[:1]
        self.assertTrue(match.is_multi)
        self.assertEqual(
            match.move_line_ids, self.payable_line(a) | self.payable_line(b)
        )
        self.assertEqual(debit.recommended_action, "link_many")
        summary = debit.action_apply_recommended()
        self.assertEqual(summary["linked"], 1)
        self.assertEqual(debit.state, "linked")
        self.assertEqual(len(debit.allocation_ids), 2)

    def test_line_in_active_order_or_linked_elsewhere_is_not_a_candidate(self):
        bill = self.make_bill(self.vendor, 333.0, self.day(5))
        first = self.upsert(self.boleto(self.vendor_cnpj, 333.0, self.day(5)))
        first.action_link(self.payable_line(bill).ids)
        second = self.upsert(self.boleto(self.vendor_cnpj, 333.0, self.day(5)))
        self.assertFalse(second.match_ids)
        self.assertIn("no_title", second.alert_codes)

    def test_document_number_formats(self):
        bill = self.make_bill(self.vendor, 250.0, self.day(5), "000321")
        debit = self.upsert(
            self.boleto(
                self.vendor_cnpj, 250.0, self.day(5), document_number="NF 321/3"
            )
        )
        self.assertIn("Same document number", debit.match_ids.evidence)
        self.assertEqual(debit.match_ids.move_line_ids, self.payable_line(bill))

    def test_different_document_number_is_not_strict(self):
        self.company.dda_auto_link = True
        self.make_bill(self.vendor, 260.0, self.day(5), "111")
        debit = self.upsert(
            self.boleto(self.vendor_cnpj, 260.0, self.day(5), document_number="222")
        )
        self.assertEqual(debit.state, "suggested")
        self.assertFalse(debit.match_ids.is_strict)

    def test_missing_number_counts_neither_way(self):
        self.company.dda_auto_link = True
        self.make_bill(self.vendor, 270.0, self.day(5))
        debit = self.upsert(self.boleto(self.vendor_cnpj, 270.0, self.day(5)))
        self.assertEqual(debit.state, "linked")
        self.assertEqual(debit.match_ids.score, 40 + 30 + 20)

    def test_amount_divergence_never_edits_the_invoice(self):
        bill = self.make_bill(self.vendor, 3500.0, self.day(10), "2002")
        debit = self.upsert(
            self.boleto(
                self.vendor_cnpj,
                3612.5,
                self.day(10),
                document_number="2002",
                interest_amount=112.5,
            )
        )
        self.assertEqual(debit.state, "suggested")
        self.assertFalse(debit.match_ids.is_strict)
        self.assertEqual(debit.divergence_amount, 112.5)
        self.assertEqual(debit.recommended_action, "review")
        debit.action_link(self.payable_line(bill).ids)
        self.assertEqual(bill.amount_total, 3500.0)
        self.assertEqual(self.payable_line(bill).amount_residual, -3500.0)
        self.assertEqual(debit.divergence_amount, 112.5)

    def test_amount_tolerance_only_suggests(self):
        self.company.write({"dda_auto_link": True, "dda_amount_tolerance": 5.0})
        self.make_bill(self.vendor, 100.0, self.day(5))
        debit = self.upsert(self.boleto(self.vendor_cnpj, 103.0, self.day(5)))
        self.assertEqual(debit.state, "suggested")
        self.assertEqual(debit.match_ids.score, 40 + 15 + 20)
        self.company.dda_amount_tolerance = 0.0

    def test_due_date_window(self):
        self.make_bill(self.vendor, 90.0, self.day(5))
        close = self.upsert(self.boleto(self.vendor_cnpj, 90.0, self.day(7)))
        self.assertEqual(close.match_ids.score, 40 + 30 + 10)
        far = self.upsert(self.boleto(self.vendor_cnpj, 90.0, self.day(20)))
        self.assertEqual(far.match_ids.score, 40 + 30)

    def test_unknown_cnpj_without_title_is_suspect_until_verified(self):
        debit = self.upsert(self.boleto(make_cnpj("833618300001"), 980.0, self.day(4)))
        self.assertEqual(debit.state, "suspect")
        self.assertTrue(debit.is_suspect)
        self.assertEqual(debit.recommended_action, "verify")
        self.assertIn("unknown_partner", debit.alert_codes)
        debit.action_mark_verified()
        self.assertFalse(debit.is_suspect)
        self.assertEqual(debit.state, "new")
        self.assertTrue(debit.verified_date)

    def test_possible_duplicate_alert(self):
        vendor_cnpj = self.vendor_cnpj
        first = self.upsert(self.boleto(vendor_cnpj, 123.0, self.day(30)))
        second = self.upsert(self.boleto(vendor_cnpj, 123.0, self.day(30)))
        self.assertIn("possible_duplicate", second.alert_codes)
        first._dda_run_matching()
        self.assertIn("possible_duplicate", first.alert_codes)

    def test_known_vendor_without_title_recommends_bill_when_enabled(self):
        self.company.dda_create_bill_mode = "draft"
        debit = self.upsert(self.boleto(self.vendor_cnpj, 45.0, self.day(2)))
        self.assertEqual(debit.state, "new")
        self.assertEqual(debit.recommended_action, "create_bill")
        self.company.dda_create_bill_mode = "never"
        debit.invalidate_recordset()
        self.assertEqual(debit.recommended_action, "review")
