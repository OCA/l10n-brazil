# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase


class TestCustomerInvoice(SavepointCase):
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
                default_debit_account_id=cls.sale_account.id,
                default_credit_account_id=cls.sale_account.id,
            )
        )
        cls.invoice_1 = cls.env["account.invoice"].create(
            dict(
                name="Test Customer Invoice",
                payment_term_id=cls.env.ref("account.account_payment_term_advance").id,
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
                                        cls.env.user.company_id.id,
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
        cls.invoice_2 = cls.env["account.invoice"].create(
            dict(
                name="Test Customer Invoice",
                payment_term_id=cls.env.ref("account.account_payment_term_advance").id,
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
                                        cls.env.user.company_id.id,
                                    ),
                                ],
                                limit=1,
                            )
                            .id,
                            "name": "product test 5",
                            "uom_id": cls.env.ref("uom.product_uom_unit").id,
                            "invoice_line_tax_ids": [
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
        cls.invoice_3 = cls.env["account.invoice"].create(
            dict(
                payment_term_id=cls.env.ref("account.account_payment_term_advance").id,
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
                                        cls.env.user.company_id.id,
                                    ),
                                ],
                                limit=1,
                            )
                            .id,
                            "name": "product test 5",
                            "uom_id": cls.env.ref("uom.product_uom_unit").id,
                            "invoice_line_tax_ids": [
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
        self.invoice_1.action_invoice_open()
        self.assertEqual(
            self.invoice_1.state, "open", "Invoice should be in state Open"
        )

    def test_tax(self):
        self.invoice_2.action_invoice_open()
        self.assertEqual(
            self.invoice_2.state, "open", "Invoice should be in state Open"
        )
        invoice_tax = self.invoice_2.tax_line_ids.sorted(key=lambda r: r.sequence)
        self.assertEqual(invoice_tax.mapped("amount"), [50.0, 550.0, 220.0])
        self.assertEqual(invoice_tax.mapped("base"), [500.0, 550.0, 1100.0])
        assert self.invoice_2.move_id, "Move not created for open invoice"
        self.invoice_2.pay_and_reconcile(
            self.env["account.journal"].search([("type", "=", "bank")], limit=1),
            10050.0,
        )
        assert (
            self.invoice_2.payment_move_line_ids
        ), "Paymente Move Line not created for Paid invoice"
        self.assertEqual(
            self.invoice_2.state, "paid", "Invoice should be in state Paid"
        )

    def test_invoice_other_currency(self):
        self.assertEqual(
            self.invoice_3.state, "draft", "Invoice should be in state Draft"
        )
        self.invoice_3.action_invoice_open()
        assert self.invoice_3.move_id, "Move Receivable not created for open invoice"
        self.assertEqual(
            self.invoice_3.state, "open", "Invoice should be in state Open"
        )

    def test_invoice_line_ids_write(self):
        self.invoice_3.invoice_line_ids.write({"invoice_id": self.invoice_3.id})
        for line in self.invoice_3.invoice_line_ids:
            self.assertEqual(
                line.document_id.id,
                self.invoice_3.fiscal_document_id.id,
                "line.document_id should be equal account.fiscal_document_id",
            )
