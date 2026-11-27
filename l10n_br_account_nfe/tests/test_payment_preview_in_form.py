# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools import format_date


@tagged("post_install", "-at_install")
class TestPaymentPreviewInForm(TransactionCase):
    """What the draft invoice previews for the payment is what the posting writes
    in the NF-e, whatever order the user fills the payment term and the payment
    mode."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        companies = cls.env["res.company"].search([])
        cls.env.user.company_ids = [Command.set(companies.ids)]
        cls.env.user.company_id = cls.company
        cls.env.user.groups_id |= cls.env.ref(
            "l10n_br_account.group_line_fiscal_detail"
        )
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Boleto",
                "company_id": cls.company.id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "fiscal_payment_mode": "15",
                "bank_account_link": "variable",
            }
        )
        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "30 Days",
                "line_ids": [Command.create({"value": "balance", "days": 30})],
            }
        )

    def _draft(self):
        form = Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        )
        form.partner_id = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        form.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        form.document_serie_id = self.env.ref(
            "l10n_br_fiscal.empresa_lc_document_55_serie_1"
        )
        with form.invoice_line_ids.new() as line:
            line.product_id = self.env.ref("product.product_product_7")
            line.price_unit = 450.0
        move = form.save()
        self.env.flush_all()
        self.env.invalidate_all()
        return move

    def _written(self, move):
        move.action_post()
        (written,) = move.nfe40_detPag
        return (written.nfe40_tPag, written.nfe40_vPag, written.nfe40_indPag)

    def test_the_preview_follows_the_payment_mode_chosen_after_the_term(self):
        move = self._draft()
        with Form(move) as form:
            form.invoice_payment_term_id = self.payment_term
            self.assertIn("90 - ", form.edi_payment_summary)

            form.payment_mode_id = self.payment_mode

            self.assertIn("15 - Boleto", form.edi_payment_summary)
            self.assertIn("In installments", form.edi_payment_summary)
            due = fields.Date.context_today(move) + timedelta(days=30)
            self.assertIn(format_date(self.env, due), form.edi_payment_summary)

        self.assertEqual(self._written(move), ("15", 450.0, "1"))
        self.assertEqual(move.nfe40_dup.nfe40_dVenc, due)
        self.assertEqual(move.nfe40_dup.nfe40_vDup, 450.0)

    def test_the_preview_follows_the_payment_mode_cleared_after_the_term(self):
        move = self._draft()
        with Form(move) as form:
            form.payment_mode_id = self.payment_mode
            form.invoice_payment_term_id = self.payment_term
            self.assertIn("15 - Boleto", form.edi_payment_summary)

            form.payment_mode_id = self.env["account.payment.mode"]

            self.assertIn("90 - ", form.edi_payment_summary)

        self.assertEqual(self._written(move), ("90", 0.0, "0"))
