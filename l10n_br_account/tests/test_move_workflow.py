# Copyright (C) 2025 Diego Paradeda - KMEE
# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# Copyright 2026 - TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_PARTNER,
    DOCUMENT_STATE_CANCEL,
)

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestMoveWorkflow(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()

        cls.move_out_venda = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )

    # FIXME migrate to v18!
    def FIXME_test_change_states(self):
        document_id = self.move_out_venda.fiscal_document_id
        self.assertEqual(self.move_out_venda.state, "draft")
        self.assertEqual(document_id.state, "em_digitacao")
        self.move_out_venda.action_post()
        self.assertEqual(self.move_out_venda.state, "posted")
        fiscal_edi = self.env["ir.module.module"].search(
            [("name", "=", "l10n_br_fiscal_edi")]
        )
        if fiscal_edi and fiscal_edi.state == "installed":
            self.assertEqual(document_id.state, "a_enviar")
            self.move_out_venda.button_draft()
            self.assertEqual(self.move_out_venda.state, "draft")
            self.assertEqual(document_id.state, "em_digitacao")
            document_id.action_document_confirm()
            self.assertEqual(self.move_out_venda.state, "posted")
            self.assertEqual(document_id.state, "a_enviar")
            document_id.action_document_back2draft()
            self.assertEqual(self.move_out_venda.state, "draft")
            self.assertEqual(document_id.state, "em_digitacao")

    # FIXME migrate to v18!
    # The FSM deny flow posts the invoice first (to reach the 'a_enviar' state
    # where a denial is valid), then denies it. The deny -> cancel_move_ids ->
    # button_cancel path resets the posted move to draft (Odoo 17+ core
    # button_cancel calls button_draft), and on 18.0 that re-balance is broken:
    # the core tax engine resets the product line balance to price_subtotal
    # (full price) while the fiscal tax lines (amount_tax_included) remain,
    # leaving the entry unbalanced ("The entry is not balanced."). Same root
    # cause as FIXME_test_change_states above.
    def FIXME_test_document_deny(self):
        document_id = self.move_out_venda.fiscal_document_id
        self.assertEqual(self.move_out_venda.state, "draft")
        # Post the invoice, which confirms the document into 'open' state.
        # Run under sudo: on 17.0 the move re-post trips the "Entry lines"
        # record rule for a non-admin test user (line company_id flush).
        self.move_out_venda.sudo().action_post()
        # Trigger deny via FSM — the _after_document_deny callback
        # in l10n_br_account cancels the linked account.move
        document_id._trigger_fsm("action_deny")
        self.assertEqual(self.move_out_venda.state, "cancel")

    def _pay(self, invoice):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create(
            {"journal_id": self.company_data["default_journal_bank"].id}
        )._create_payments()

    def test_a_paid_invoice_the_sefaz_voided_needs_a_manual_settlement(self):
        self.move_out_venda.action_post()
        self._pay(self.move_out_venda)
        self.assertEqual(self.move_out_venda.payment_state, "paid")

        self.move_out_venda.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL

        self.assertEqual(
            self.move_out_venda._settled_moves_no_longer_valid(), self.move_out_venda
        )

    def test_an_unpaid_invoice_the_sefaz_voided_is_left_alone(self):
        self.move_out_venda.action_post()
        self.assertEqual(self.move_out_venda.payment_state, "not_paid")

        self.move_out_venda.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL

        self.assertFalse(self.move_out_venda._settled_moves_no_longer_valid())

    def _source_cancel_notes(self, move):
        return move.message_ids.filtered(
            lambda message: "cancelled at the source" in (message.body or "")
        )

    def _source_cancel_alerts(self, move):
        activity_type = self.env.ref(
            "l10n_br_account.mail_activity_fiscal_document_cancelled_at_source"
        )
        return move.activity_ids.filtered(
            lambda activity: activity.activity_type_id == activity_type
        )

    def _cancel_imported_at_source(self, bill):
        bill.fiscal_document_id.with_context(lang="en_US").write(
            {"state_edoc": DOCUMENT_STATE_CANCEL}
        )

    def _posted_imported_vendor_bill(self, number):
        bill = self.init_invoice(
            "in_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                self.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number=number,
            post=True,
        )
        self.assertEqual(bill.issuer, DOCUMENT_ISSUER_PARTNER)
        self.assertEqual(bill.state, "posted")
        bill.fiscal_document_id.imported_document = True
        return bill

    def test_the_list_shows_every_fiscal_status(self):
        labels = dict(
            self.env["l10n_br_fiscal.document"]
            ._fields["state_edoc"]
            ._description_selection(self.env)
        )
        self.assertEqual(
            self.move_out_venda.fiscal_document_status,
            labels[self.move_out_venda.state_edoc],
        )
        self.move_out_venda.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL
        self.assertEqual(
            self.move_out_venda.fiscal_document_status,
            labels[DOCUMENT_STATE_CANCEL],
        )
        bare = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_a.id,
            }
        )
        self.assertFalse(bare.fiscal_document_id)
        self.assertFalse(bare.fiscal_document_status)

    def test_cancelling_an_imported_document_notes_the_posted_bill_once(self):
        bill = self._posted_imported_vendor_bill("88001")
        bill.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL

        self.assertEqual(bill.state, "posted")
        self.assertEqual(bill.state_edoc, DOCUMENT_STATE_CANCEL)
        notes = self._source_cancel_notes(bill)
        self.assertEqual(len(notes), 1)
        self.assertIn("decide how to handle it.", notes.body)

        bill.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL
        self.assertEqual(len(self._source_cancel_notes(bill)), 1)

    def test_a_paid_imported_bill_asks_for_a_manual_settlement(self):
        bill = self._posted_imported_vendor_bill("88002")
        self._pay(bill)
        self.assertIn(bill.payment_state, ("paid", "partial", "in_payment"))

        bill.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL

        self.assertEqual(bill.state, "posted")
        notes = self._source_cancel_notes(bill)
        self.assertEqual(len(notes), 1)
        self.assertIn("decide how to handle it.", notes.body)

    def test_an_imported_cancelled_bill_cannot_be_drafted_or_paid(self):
        bill = self._posted_imported_vendor_bill("88003")
        bill.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL

        with self.assertRaises(UserError):
            bill.button_draft()
        self.assertEqual(bill.state, "posted")
        self.assertEqual(bill.state_edoc, DOCUMENT_STATE_CANCEL)

        with self.assertRaises(UserError):
            bill.action_register_payment()
        self.assertEqual(bill.state, "posted")

    def test_a_company_invoice_cancel_does_not_note_the_bill(self):
        self.move_out_venda.action_post()
        self.move_out_venda.fiscal_document_id.state_edoc = DOCUMENT_STATE_CANCEL
        self.assertFalse(self._source_cancel_notes(self.move_out_venda))
        self.assertFalse(self._source_cancel_alerts(self.move_out_venda))

    def test_a_local_cancel_does_not_use_the_source_wording(self):
        bill = self._posted_imported_vendor_bill("88004")
        bill.button_cancel()
        self.assertEqual(bill.state_edoc, DOCUMENT_STATE_CANCEL)
        self.assertFalse(self._source_cancel_notes(bill))
        self.assertFalse(self._source_cancel_alerts(bill))

    def test_a_posted_imported_bill_gets_one_source_cancel_alert(self):
        salesperson = self.env["res.users"].create(
            {
                "name": "Source Cancel Salesperson",
                "login": "source_cancel_salesperson",
                "email": "source_cancel_salesperson@example.com",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        bill = self._posted_imported_vendor_bill("88011")
        bill.invoice_user_id = salesperson
        self._cancel_imported_at_source(bill)

        alerts = self._source_cancel_alerts(bill)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts.user_id, salesperson)
        self.assertIn("decide how to handle it.", str(alerts.note))

        self._cancel_imported_at_source(bill)
        self.assertEqual(len(self._source_cancel_alerts(bill)), 1)

    def test_the_alert_uses_the_bill_creator_without_a_salesperson(self):
        bill = self._posted_imported_vendor_bill("88013")
        bill.invoice_user_id = False
        self._cancel_imported_at_source(bill)
        self.assertEqual(self._source_cancel_alerts(bill).user_id, bill.create_uid)

    def test_a_draft_imported_bill_gets_no_source_cancel_alert(self):
        bill = self.init_invoice(
            "in_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                self.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="88014",
        )
        self.assertEqual(bill.state, "draft")
        self.assertEqual(bill.issuer, DOCUMENT_ISSUER_PARTNER)
        bill.fiscal_document_id.imported_document = True
        self._cancel_imported_at_source(bill)
        self.assertFalse(self._source_cancel_alerts(bill))
