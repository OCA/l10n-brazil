# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import SavepointCase


class TestSupplierInvoice(SavepointCase):
    """
    This is a simple test for ensuring l10n_br_account doesn't break the basic
    account module behavior with supplier invoices.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_account = cls.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Purchase - (test)",
                user_type_id=cls.env.ref("account.data_account_type_revenue").id,
            )
        )

        cls.purchase_journal = cls.env["account.journal"].create(
            dict(
                name="Purchase Journal - (test)",
                code="TPJ",
                type="purchase",
                refund_sequence=True,
                default_account_id=cls.purchase_account.id,
            )
        )

        cls.invoice_1 = cls.env["account.move"].create(
            dict(
                name="Test Supplier Invoice 1",
                move_type="in_invoice",
                invoice_date=fields.Date.today(),
                partner_id=cls.env.ref("base.res_partner_3").id,
                journal_id=cls.purchase_journal.id,
                invoice_line_ids=[
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_5").id,
                            "quantity": 10.0,
                            "price_unit": 450.0,
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
                            "name": "product test 5",
                            "uom_id": cls.env.ref("uom.product_uom_unit").id,
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
