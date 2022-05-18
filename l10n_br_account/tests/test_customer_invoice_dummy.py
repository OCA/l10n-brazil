# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase


class TestCustomerInvoice(SavepointCase):
    """
    This is a simple test for ensuring l10n_br_account doesn't break the basic
    account module behavior with customer invoices.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_account = cls.env["account.account"].create(
            dict(
                code="X1020",
                name="Product Sales - (test)",
                user_type_id=cls.env.ref("account.data_account_type_revenue").id,
                reconcile=True,
            )
        )

        cls.sale_journal = cls.env["account.journal"].create(
            dict(
                name="Sales Journal - (test)",
                code="TSAJ",
                type="sale",
                refund_sequence=True,
                default_account_id=cls.sale_account.id,
            )
        )

        cls.invoice_1 = cls.env["account.move"].create(
            dict(
                name="Test Customer Invoice 1",
                move_type="out_invoice",
                partner_id=cls.env.ref("base.res_partner_3").id,
                journal_id=cls.sale_journal.id,
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

        # Invoice with TAXES
        tax_fixed = cls.env["account.tax"].create(
            {
                "sequence": 10,
                "name": "Tax 10.0 (Fixed)",
                "amount": 10.0,
                "amount_type": "fixed",
                "include_base_amount": True,
            }
        )

        tax_percent_included_base_incl = cls.env["account.tax"].create(
            {
                "sequence": 20,
                "name": "Tax 50.0% (Percentage of Price Tax Included)",
                "amount": 50.0,
                "amount_type": "division",
                "include_base_amount": True,
            }
        )

        tax_percentage = cls.env["account.tax"].create(
            {
                "sequence": 30,
                "name": "Tax 20.0% (Percentage of Price)",
                "amount": 20.0,
                "amount_type": "percent",
                "include_base_amount": False,
            }
        )

        cls.invoice_2 = cls.env["account.move"].create(
            dict(
                name="Test Customer Invoice 2",
                move_type="out_invoice",
                partner_id=cls.env.ref("base.res_partner_3").id,
                journal_id=cls.sale_journal.id,
                invoice_line_ids=[
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_5").id,
                            "quantity": 5.0,
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
                            "name": "product test 5",
                            "uom_id": cls.env.ref("uom.product_uom_unit").id,
                            "tax_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        tax_fixed.id,
                                        tax_percent_included_base_incl.id,
                                        tax_percentage.id,
                                    ],
                                )
                            ],
                        },
                    )
                ],
            )
        )

        tax_discount = cls.env["account.tax"].create(
            {
                "sequence": 40,
                "name": "Tax 20.0% (Discount)",
                "amount": 20.0,
                "amount_type": "percent",
                "include_base_amount": False,
            }
        )

        cls.invoice_3 = cls.env["account.move"].create(
            dict(
                name="Test Customer Invoice 3",
                move_type="out_invoice",
                currency_id=cls.env.ref("base.EUR").id,
                partner_id=cls.env.ref("base.res_partner_3").id,
                journal_id=cls.sale_journal.id,
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
                            "tax_ids": [
                                (
                                    6,
                                    0,
                                    [
                                        tax_discount.id,
                                        tax_percent_included_base_incl.id,
                                        tax_percentage.id,
                                    ],
                                )
                            ],
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

    def test_post(self):
        self.invoice_2.action_post()
        self.assertEqual(
            self.invoice_2.state, "posted", "Invoice should be in state posted"
        )

    def test_invoice_other_currency(self):
        self.assertEqual(
            self.invoice_3.state, "draft", "Invoice should be in state Draft"
        )
        self.invoice_3.action_post()
        self.assertEqual(
            self.invoice_3.state, "posted", "Invoice should be in state posted"
        )

    def test_line_ids_write(self):
        self.invoice_3.invoice_line_ids.write({"move_id": self.invoice_3.id})
        for line in self.invoice_3.invoice_line_ids:
            self.assertEqual(
                line.document_id.id,
                self.invoice_3.fiscal_document_id.id,
                "line.document_id should be equal invoice fiscal_document_id",
            )
