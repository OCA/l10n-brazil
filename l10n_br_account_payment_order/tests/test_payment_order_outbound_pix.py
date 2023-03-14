# Copyright (C) 2022 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentOrderOutboundPIX(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        cls.env.user.company_id = cls.company.id
        cls.res_partner_bank_model = cls.env["res.partner.bank"]
        cls.payment_mode_model = cls.env["account.payment.mode"]
        cls.payment_order_model = cls.env["account.payment.order"]
        cls.payment_line_model = cls.env["account.payment.line"]
        cls.res_partner_pix_model = cls.env["res.partner.pix"]
        cls.bank_001 = cls.env.ref("l10n_br_base.res_bank_001")
        cls.res_partner_pix_model.create(
            {
                "partner_id": cls.partner_a.id,
                "key_type": "phone",
                "key": "+50372424737",
            }
        )
        cls.outbound_payment_method = cls.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240_out"
        )
        cls.pix_mode = cls.payment_mode_model.create(
            {
                "bank_account_link": "variable",
                "name": "Pix Transfer",
                "company_id": cls.company.id,
                "payment_method_id": cls.outbound_payment_method.id,
                "payment_mode_domain": "pix_transfer",
                "payment_order_ok": True,
                "variable_journal_ids": cls.company_data["default_journal_bank"],
            }
        )
        cls.ted_mode = cls.payment_mode_model.create(
            {
                "bank_account_link": "variable",
                "name": "TED Transfer",
                "company_id": cls.company.id,
                "payment_method_id": cls.outbound_payment_method.id,
                "payment_mode_domain": "ted",
                "payment_order_ok": True,
                "variable_journal_ids": cls.company_data["default_journal_bank"],
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "partner_id": cls.partner_a.id,
                "move_type": "in_invoice",
                "ref": "Test Bill Invoice 1",
                "invoice_date": fields.Date.today(),
                "company_id": cls.company.id,
                "payment_mode_id": cls.pix_mode.id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_a.id,
                            "quantity": 1.0,
                            "price_unit": 300.0,
                        },
                    )
                ],
            }
        )
        # Make sure no other payment orders are in the DB
        cls.domain = [
            ("state", "=", "draft"),
            ("payment_type", "=", "outbound"),
            ("company_id", "=", cls.company.id),
        ]
        cls.payment_order_model.search(cls.domain).unlink()

    def test_pix_payment_order(self):
        # Open invoice
        self.invoice.action_post()
        # Add to payment order using the wizard
        self.env["account.invoice.payment.line.multi"].with_context(
            active_model="account.move", active_ids=self.invoice.ids
        ).create({}).run()

        payment_order = self.env["account.payment.order"].search(self.domain)
        self.assertEqual(len(payment_order), 1)

        self.assertEqual(
            payment_order.payment_line_ids.partner_pix_id.key, "+50372424737"
        )
        self.assertEqual(payment_order.payment_line_ids.pix_transfer_type, "pix_key")

        payment_order.write(
            {"journal_id": self.company_data["default_journal_bank"].id}
        )

        self.assertEqual(len(payment_order.payment_line_ids), 1)

        # Open payment order
        payment_order.draft2open()

    def test_payment_line_change_partner(self):
        payorder = self.payment_order_model.create(
            {"payment_mode_id": self.pix_mode.id}
        )
        payline = self.payment_line_model.create(
            {
                "communication_type": "normal",
                "partner_id": self.partner_a.id,
                "order_id": payorder.id,
            }
        )
        payline.partner_id_change()
        self.assertEqual(payline.partner_pix_id.key, "+50372424737")

        payline.partner_id = self.partner_b
        payline.partner_id_change()
        self.assertFalse(payline.partner_pix_id.key)
        with self.assertRaises(UserError):
            payline._check_pix_transfer_type()

    def test_pix_transfer_false_type(self):
        payorder = self.payment_order_model.create(
            {"payment_mode_id": self.ted_mode.id}
        )
        payline = self.payment_line_model.create(
            {
                "communication_type": "normal",
                "partner_id": self.partner_a.id,
                "order_id": payorder.id,
            }
        )
        payline.partner_id_change()
        payline._compute_pix_transfer_type()
        self.assertFalse(payline.pix_transfer_type)

    def test_pix_transfer_acc_type(self):
        self.res_partner_bank_model.create(
            {
                "bank_id": self.bank_001.id,
                "acc_number": "1278928 121268712 127",
                "partner_id": self.partner_b.id,
                "transactional_acc_type": "payment",
            }
        )
        payorder = self.payment_order_model.create(
            {"payment_mode_id": self.pix_mode.id}
        )
        payline = self.payment_line_model.create(
            {
                "communication_type": "normal",
                "partner_id": self.partner_b.id,
                "order_id": payorder.id,
            }
        )
        payline.partner_id_change()
        payline._compute_pix_transfer_type()
        self.assertEqual(payline.pix_transfer_type, "payment")
