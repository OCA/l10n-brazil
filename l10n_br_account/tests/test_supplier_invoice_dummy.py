# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests.common import TransactionCase


class TestSupplierInvoice(TransactionCase):
    """
    This is a simple test for ensuring l10n_br_account doesn't break the basic
    account module behavior with supplier invoices.
    """

    def setUp(self):
        super().setUp()
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
                default_account_id=self.purchase_account.id,
            )
        )

        self.invoice_1 = self.env["account.move"].create(
            dict(
                name="Test Supplier Invoice 1",
                move_type="in_invoice",
                invoice_date=fields.Date.today(),
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
                                        self.env.company.id,
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
        self.invoice_1.action_post()
        self.assertEqual(
            self.invoice_1.state, "posted", "Invoice should be in state posted"
        )
