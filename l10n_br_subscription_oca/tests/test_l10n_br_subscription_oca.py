# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nBrSubscriptionOca(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env.ref("l10n_br_base.res_partner_kmee")
        cls.fo_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.product_service = cls.env.ref("l10n_br_fiscal.customized_development_sale")
        cls.product_goods = cls.env.ref("product.product_delivery_01")
        cls.template = cls.env.ref(
            "l10n_br_subscription_oca.subscription_template_monthly"
        )

    def _create_subscription(self, products, fiscal_operation):
        """Through the form, so the lines get the fiscal defaults of the view."""
        form = Form(self.env["sale.subscription"])
        form.partner_id = self.partner
        form.template_id = self.template
        form.fiscal_operation_id = fiscal_operation
        for product in products:
            with form.sale_subscription_line_ids.new() as line:
                line.product_id = product
                line.price_unit = 100.0
        return form.save()

    def test_invoice_with_fiscal_document(self):
        subscription = self._create_subscription([self.product_service], self.fo_venda)
        line = subscription.sale_subscription_line_ids
        self.assertEqual(line.fiscal_operation_id, self.fo_venda)
        self.assertTrue(line.fiscal_operation_line_id)
        self.assertTrue(line.fiscal_tax_ids)

        invoice = subscription.create_invoice()
        self.assertEqual(invoice.fiscal_operation_id, self.fo_venda)
        self.assertEqual(
            invoice.document_type_id,
            line.fiscal_operation_line_id.get_document_type(subscription.company_id),
        )
        self.assertTrue(invoice.document_serie_id)
        invoice_line = invoice.invoice_line_ids
        self.assertEqual(
            invoice_line.fiscal_operation_line_id, line.fiscal_operation_line_id
        )
        self.assertEqual(invoice_line.fiscal_tax_ids, line.fiscal_tax_ids)
        self.assertAlmostEqual(invoice.amount_total, subscription.amount_total)

    def test_lines_created_by_code_inherit_the_fiscal_operation(self):
        subscription = self.env["sale.subscription"].create(
            {
                "partner_id": self.partner.id,
                "template_id": self.template.id,
                "pricelist_id": self.env.ref(
                    "l10n_br_subscription_oca.pricelist_subscription"
                ).id,
                "fiscal_operation_id": self.fo_venda.id,
                "sale_subscription_line_ids": [
                    Command.create(
                        {"product_id": self.product_service.id, "price_unit": 100.0}
                    )
                ],
            }
        )
        line = subscription.sale_subscription_line_ids
        self.assertEqual(line.fiscal_operation_id, self.fo_venda)
        self.assertTrue(line.fiscal_operation_line_id)
        self.assertTrue(line.fiscal_tax_ids)
        invoice = subscription.create_invoice()
        self.assertEqual(
            invoice.document_type_id,
            line.fiscal_operation_line_id.get_document_type(subscription.company_id),
        )
        self.assertAlmostEqual(invoice.amount_total, subscription.amount_total)
        self.assertTrue(invoice.amount_total)

    def test_invoice_without_fiscal_operation(self):
        subscription = self._create_subscription(
            [self.product_service], self.env["l10n_br_fiscal.operation"]
        )
        self.assertFalse(subscription.sale_subscription_line_ids.fiscal_operation_id)
        invoice = subscription.create_invoice()
        self.assertFalse(invoice.fiscal_operation_id)
        self.assertFalse(invoice.document_type_id)
        self.assertFalse(invoice.invoice_line_ids.fiscal_operation_line_id)

    def test_invoice_refuses_mixed_document_types(self):
        subscription = self._create_subscription(
            [self.product_service, self.product_goods], self.fo_venda
        )
        with self.assertRaises(UserError):
            subscription.create_invoice()

    def test_sale_order_to_subscription(self):
        self.product_service.subscribable = True
        self.product_service.subscription_template_id = self.template
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "fiscal_operation_id": self.fo_venda.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_service.id,
                            "product_uom_qty": 2,
                            "price_unit": 100.0,
                            "fiscal_operation_id": self.fo_venda.id,
                        }
                    )
                ],
            }
        )
        order.with_context(uid=self.env.uid).action_confirm()
        subscription = order.subscription_ids
        self.assertEqual(subscription.fiscal_operation_id, self.fo_venda)
        self.assertEqual(
            subscription.sale_subscription_line_ids.fiscal_operation_line_id,
            order.order_line.fiscal_operation_line_id,
        )

    def test_subscription_to_sale_order(self):
        subscription = self._create_subscription([self.product_service], self.fo_venda)
        order = subscription.create_sale_order()
        self.assertEqual(order.fiscal_operation_id, self.fo_venda)
        self.assertEqual(
            order.order_line.fiscal_operation_line_id,
            subscription.sale_subscription_line_ids.fiscal_operation_line_id,
        )
