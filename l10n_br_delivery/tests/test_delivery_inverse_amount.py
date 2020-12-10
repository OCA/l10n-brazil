# @ 2020 KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase, Form


class TestDeliveryInverseAmount(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a new sale order
        sale_order_form = Form(self.env['sale.order'], 'sale.view_order_form')
        sale_order_form.partner_id = self.env.ref(
            'l10n_br_base.res_partner_kmee')
        self.sale_order_id = sale_order_form.save()

        # Set 2 different products to the sale order
        with Form(self.sale_order_id) as so:
            with so.order_line.new() as line:
                line.product_id = self.env.ref('product.product_delivery_01')
            with so.order_line.new() as line:
                line.product_id = self.env.ref('product.product_delivery_02')

        # Change freight amount, insurance and other costs values
        with Form(self.sale_order_id) as so:
            so.amount_freight = 100.0
            so.amount_insurance = 100.0
            so.amount_costs = 100.0

        # Confirm and create invoice for the sale order
        self.sale_order_id.action_confirm()

        for move in self.sale_order_id.picking_ids.mapped(
                'move_ids_without_package'):
            move.quantity_done = move.product_uom_qty

        for picking in self.sale_order_id.picking_ids.filtered(
                lambda p: p.state == 'confirmed'):
            picking.button_validate()

        wizard = self.env['sale.advance.payment.inv'].with_context(
            {'active_ids': self.sale_order_id.ids}).create({})

        wizard.create_invoices()

    def test_sale_order_amounts(self):
        """Check sale order amounts"""
        self.assertEqual(
            self.sale_order_id.amount_gross, 110.0,
            "Unexpected value for the field amount_gross from Sale Order")
        self.assertEqual(
            self.sale_order_id.amount_untaxed, 110.0,
            "Unexpected value for the field amount_untaxed from Sale Order")
        self.assertEqual(
            self.sale_order_id.amount_freight, 100.0,
            "Unexpected value for the field amount_freight from Sale Order")
        self.assertEqual(
            self.sale_order_id.amount_insurance, 100.0,
            "Unexpected value for the field amount_insurance from Sale Order")
        self.assertEqual(
            self.sale_order_id.amount_costs, 100.0,
            "Unexpected value for the field amount_costs from Sale Order")
        self.assertEqual(
            self.sale_order_id.amount_tax, 0.0,
            "Unexpected value for the field amount_tax from Sale Order")

    def test_invoice_amount_tax(self):
        """Check invoice amount tax"""
        invoice_tax = self.sale_order_id.invoice_ids[0].amount_tax

        self.assertEqual(
            invoice_tax, 300,
            "Unexpected value for the field invoice_tax from Invoice")

    def test_inverse_amount_freight(self):
        """Check Fiscal Document freight values"""
        fiscal_document_id = \
            self.sale_order_id.invoice_ids[0].fiscal_document_id
        self.assertEqual(
            fiscal_document_id.amount_freight_value, 100,
            "Unexpected value for the field amount_freight_value from "
            "Fiscal Document")

        for line in fiscal_document_id.line_ids:
            if line.name == '[FURN_7777] Office Chair':
                self.assertEqual(
                    line.freight_value, 63.64,
                    "Unexpected value for the field freight_value from "
                    "Fiscal Document line")
            if line.name == '[FURN_8888] Office Lamp':
                self.assertEqual(
                    line.freight_value, 36.36,
                    "Unexpected value for the field freight_value from "
                    "Fiscal Document line")

    def test_inverse_amount_insurance(self):
        """Check Fiscal Document insurance values"""
        fiscal_document_id = \
            self.sale_order_id.invoice_ids[0].fiscal_document_id
        self.assertEqual(
            fiscal_document_id.amount_insurance_value, 100,
            "Unexpected value for the field amount_insurance_value from "
            "Fiscal Document")

        for line in fiscal_document_id.line_ids:
            if line.name == '[FURN_7777] Office Chair':
                self.assertEqual(
                    line.insurance_value, 63.64,
                    "Unexpected value for the field insurance_value from "
                    "Fiscal Document line")
            if line.name == '[FURN_8888] Office Lamp':
                self.assertEqual(
                    line.insurance_value, 36.36,
                    "Unexpected value for the field insurance_value from "
                    "Fiscal Document line")

    def test_inverse_amount_other_costs(self):
        """Check Fiscal Document other costs values"""
        fiscal_document_id = \
            self.sale_order_id.invoice_ids[0].fiscal_document_id
        self.assertEqual(
            fiscal_document_id.amount_other_costs_value, 100,
            "Unexpected value for the field other_costs_value from "
            "Fiscal Document")

        for line in fiscal_document_id.line_ids:
            if line.name == '[FURN_7777] Office Chair':
                self.assertEqual(
                    line.other_costs_value, 63.64,
                    "Unexpected value for the field other_costs_value from "
                    "Fiscal Document line")
            if line.name == '[FURN_8888] Office Lamp':
                self.assertEqual(
                    line.other_costs_value, 36.36,
                    "Unexpected value for the field other_costs_value from "
                    "Fiscal Document line")
