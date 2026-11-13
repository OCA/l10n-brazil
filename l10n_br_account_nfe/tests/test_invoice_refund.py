# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command, fields
from odoo.tests import Form, tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon

from .tools import load_account_nfe_fixture_files


@tagged("post_install", "-at_install")
class TestInvoiceRefund(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        if not cls.env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        ):
            load_account_nfe_fixture_files(cls.env)

        cls.configure_normal_company_taxes()
        cls.env.flush_all()

        cls.sale_account = cls.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Refund Sales - (test)",
                account_type="income",
            )
        )

        cls.refund_journal = cls.env["account.journal"].create(
            dict(
                name="Refund Journal - (test)",
                code="TREJ",
                type="sale",
                refund_sequence=True,
                default_account_id=cls.sale_account.id,
            )
        )

        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Direct debit refund",
                "company_id": cls.company_data["company"].id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "bank_account_link": "variable",
            }
        )

        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "Immediate Payment",
                "line_ids": [
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 100,
                            "delay_type": "days_after",
                            "nb_days": 0,
                        }
                    )
                ],
            }
        )

        cls.reverse_vals = {
            "date": fields.Date.from_string("2019-02-01"),
            "reason": "no reason",
            "journal_id": cls.refund_journal.id,
        }

        # Create invoice using Form (init_invoice triggers tax computation bug)
        move_form = Form(
            cls.env["account.move"].with_context(
                default_move_type="out_invoice",
                account_predictive_bills_disable_prediction=True,
            )
        )
        move_form.partner_id = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        move_form.journal_id = cls.refund_journal
        move_form.invoice_payment_term_id = cls.payment_term
        move_form.document_type_id = cls.env.ref("l10n_br_fiscal.document_55")
        move_form.document_serie_id = cls.empresa_lc_document_55_serie_1
        # l10n_latam_invoice_document compatibility
        if "l10n_latam.document.type" in cls.env:
            latam_doc_type = cls.env["l10n_latam.document.type"].search(
                [("code", "=", "55"), ("country_id", "=", cls.env.ref("base.br").id)],
                limit=1,
            )
            if latam_doc_type and move_form.l10n_latam_use_documents:
                move_form.l10n_latam_document_type_id = latam_doc_type
        move_form.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        move_form.invoice_date = "2019-02-01"
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.env.ref("product.product_product_6")
            line_form.price_unit = 100.0
            line_form.name = "Refund Test"
            line_form.fiscal_operation_line_id = cls.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            )
        cls.invoice = move_form.save()

    def test_refund_with_payment_mode(self):
        payment_mode = self.payment_mode

        invoice = self.invoice
        invoice.action_post()

        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "reason": "Estorno com boleto",
                    "journal_id": self.refund_journal.id,
                    "payment_mode_id": payment_mode.id,
                }
            )
        )

        self.assertEqual(
            move_reversal.payment_mode_id.id,
            payment_mode.id,
        )

        reversal_result = move_reversal.reverse_moves()
        reverse_move = self.env["account.move"].browse(reversal_result["res_id"])

        self.assertEqual(
            reverse_move.payment_mode_id.id,
            payment_mode.id,
        )
