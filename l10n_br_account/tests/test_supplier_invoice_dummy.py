# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestSupplierInvoice(TransactionCase):
    def setUp(self):
        super(TestSupplierInvoice, self).setUp()
        self.purchase_account = self.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Purchase - (test)",
                user_type_id=self.env.ref("account.data_account_type_revenue").id,
            )
        )

        self.purchase_journal = self.env["account.journal"].create(
            dict(
                name="Purchase Journal - (test)",
                code="TPJ",
                type="purchase",
                refund_sequence=True,
                default_debit_account_id=self.purchase_account.id,
                default_credit_account_id=self.purchase_account.id,
            )
        )
        self.invoice_1 = self.env["account.invoice"].create(
            dict(
                name="Test Supplier Invoice",
                payment_term_id=self.env.ref("account.account_payment_term_advance").id,
                partner_id=self.env.ref("base.res_partner_3").id,
                journal_id=self.purchase_journal.id,
                invoice_line_ids=[
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_5").id,
                            "quantity": 10.0,
                            "price_unit": 450.0,
                            "account_id": self.env["account.account"]
                            .search(
                                [
                                    (
                                        "user_type_id",
                                        "=",
                                        self.env.ref(
                                            "account.data_account_type_revenue"
                                        ).id,
                                    ),
                                    (
                                        "company_id",
                                        "=",
                                        self.env.user.company_id.id,
                                    ),
                                ],
                                limit=1,
                            )
                            .id,
                            "name": "product test 5",
                            "uom_id": self.env.ref("uom.product_uom_unit").id,
                        },
                    )
                ],
            )
        )

    def test_state(self):
        self.assertEqual(
            self.invoice_1.state, "draft", "Invoice should be in state Draft"
        )
        self.invoice_1.action_invoice_open()
        assert self.invoice_1.move_id, "Move Receivable not created for open invoice"
        self.assertEqual(
            self.invoice_1.state, "open", "Invoice should be in state Open"
        )
