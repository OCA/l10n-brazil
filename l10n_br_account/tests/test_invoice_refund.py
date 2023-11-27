# Copyright (C) 2021  Ygor Carvalho - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestInvoiceRefund(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.sale_account = cls.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Refund Sales - (test)",
                user_type_id=cls.env.ref("account.data_account_type_revenue").id,
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

        cls.reverse_vals = {
            "date": fields.Date.from_string("2019-02-01"),
            "reason": "no reason",
            "refund_method": "refund",
            "journal_id": cls.refund_journal.id,
        }

        cls.invoice = cls.env["account.move"].create(
            dict(
                name="Test Refund Invoice",
                move_type="out_invoice",
                invoice_payment_term_id=cls.env.ref(
                    "account.account_payment_term_advance"
                ).id,
                partner_id=cls.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                journal_id=cls.refund_journal.id,
                document_type_id=cls.env.ref("l10n_br_fiscal.document_55").id,
                document_serie_id=cls.env.ref(
                    "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                ).id,
                invoice_line_ids=[
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_6").id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "account_id": cls.env["account.account"]
                            .search(
                                [
                                    (
                                        "user_type_id",
                                        "=",
                                        cls.env.ref(
                                            "account.data_account_type_revenue"
                                        ).id,
                                    ),
                                    (
                                        "company_id",
                                        "=",
                                        cls.env.company.id,
                                    ),
                                ],
                                limit=1,
                            )
                            .id,
                            "name": "Refund Test",
                            "uom_id": cls.env.ref("uom.product_uom_unit").id,
                        },
                    )
                ],
            )
        )

    def test_refund(self):
        reverse_vals = self.reverse_vals

        invoice = self.invoice
        self.assertEqual(
            invoice.state,
            "draft",
            "Invoice should be in state Draft",
        )

        invoice.action_post()
        self.assertEqual(
            invoice.state,
            "posted",
            "Invoice should be in state Posted",
        )

        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(reverse_vals)
        )

        with self.assertRaises(UserError):
            move_reversal.reverse_moves()

        invoice["fiscal_operation_id"] = (self.env.ref("l10n_br_fiscal.fo_venda").id,)

        with self.assertRaises(UserError):
            move_reversal.reverse_moves()

        for line_id in invoice.invoice_line_ids:
            line_id["fiscal_operation_id"] = (
                self.env.ref("l10n_br_fiscal.fo_venda").id,
            )
            line_id["fiscal_operation_line_id"] = self.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            ).id

        reversal = move_reversal.reverse_moves()
        reverse_move = self.env["account.move"].browse(reversal["res_id"])

        self.assertTrue(reverse_move)

        self.assertEqual(
            reverse_move.operation_name,
            "Devolução de Venda",
            "The refund process was unsuccessful.",
        )

    def test_refund_force_fiscal_operation(self):
        reverse_vals = self.reverse_vals
        invoice = self.invoice

        invoice["fiscal_operation_id"] = (self.env.ref("l10n_br_fiscal.fo_venda").id,)

        for line_id in invoice.invoice_line_ids:
            line_id["fiscal_operation_id"] = (
                self.env.ref("l10n_br_fiscal.fo_venda").id,
            )
            line_id["fiscal_operation_line_id"] = self.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            ).id

        invoice.action_post()
        self.assertEqual(
            invoice.state,
            "posted",
            "Invoice should be in state Posted",
        )

        reverse_vals.update(
            {
                "force_fiscal_operation_id": self.env.ref(
                    "l10n_br_fiscal.fo_simples_remessa"
                ).id
            }
        )
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(reverse_vals)
        )

        reversal = move_reversal.reverse_moves()
        reverse_move = self.env["account.move"].browse(reversal["res_id"])

        self.assertTrue(reverse_move)

        self.assertEqual(
            reverse_move.operation_name,
            "Simples Remessa",
            "The force fiscal operation process was unsuccessful.",
        )
