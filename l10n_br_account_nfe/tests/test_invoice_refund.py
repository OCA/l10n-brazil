# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command, fields
from odoo.tests import TransactionCase


class TestInvoiceRefund(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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

        cls.reverse_vals = {
            "date": fields.Date.from_string("2019-02-01"),
            "reason": "no reason",
            "refund_method": "refund",
            "journal_id": cls.refund_journal.id,
        }

        cls.invoice = cls.env["account.move"].create(
            dict(
                name="Test Refund Invoice 2",
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
                    Command.create(
                        {
                            "product_id": cls.env.ref("product.product_product_6").id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "account_id": cls.env["account.account"]
                            .search(
                                [
                                    (
                                        "account_type",
                                        "=",
                                        "income",
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

    def test_refund_with_payment_mode(self):
        payment_mode = self.env.ref("account_payment_mode.payment_mode_inbound_dd1")

        invoice = self.invoice

        invoice.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda").id
        for line in invoice.invoice_line_ids:
            line.fiscal_operation_id = invoice.fiscal_operation_id
            line.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            ).id

        invoice.action_post()

        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "reason": "Estorno com boleto",
                    "refund_method": "refund",
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
