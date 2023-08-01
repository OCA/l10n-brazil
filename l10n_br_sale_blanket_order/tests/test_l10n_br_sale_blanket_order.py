# Copyright 2023 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.tests.common import SavepointCase


class L10nBrSaleBLanketOrderTest(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Set up some test data like partner, payment term, company, pricelist, etc.
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.payment_term = cls.env.ref("account.account_payment_term_immediate")
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.pricelist = cls.env.ref("product.list0")
        cls.validity_date = date.today() + timedelta(days=2)

        cls.product = cls.env.ref("product.product_product_27")
        cls.product_uom = cls.env.ref("uom.product_uom_unit")

    # Helper method to create a new Blanket Order for testing.
    def _create_blanket_order(self):
        values = {
            "partner_id": self.partner.id,
            "validity_date": self.validity_date,
            "payment_term_id": self.payment_term.id,
            "pricelist_id": self.pricelist.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom": self.product_uom.id,
                        "original_uom_qty": 20.0,
                        "price_unit": 25.0,
                    },
                )
            ],
        }
        # Create new register blanket.order
        blanket_order = self.env["sale.blanket.order"].create(values)
        blanket_order.sudo().onchange_partner_id()

        return blanket_order

    # Helper method to create a new wizard for testing, based on a Blanket Order.
    def _create_wizard(self, blanket_order):
        lines = []
        for line in blanket_order.line_ids:
            line_vals = {
                "blanket_line_id": line.id,
                "product_id": line.product_id.id,
                "date_schedule": line.date_schedule,
                "remaining_uom_qty": line.remaining_uom_qty,
                "price_unit": line.price_unit,
                "product_uom": line.product_uom,
                "qty": line.remaining_uom_qty,
                "partner_id": line.partner_id,
            }
            lines.append((0, 0, line_vals))

        # Create a new wizard record for the given Blanket Order
        wizard = (
            self.env["sale.blanket.order.wizard"]
            .with_context(active_id=blanket_order.id, active_model="sale.blanket.order")
            .create(
                {
                    "blanket_order_id": blanket_order.id,
                    "line_ids": lines,
                }
            )
        )

        return wizard

    # Test method to confirm and process a Blanket Order.
    def test_confirm_and_process_blanket_order_and_invoice(self):
        # Create a new Blanket Order for testing
        blanket_order = self._create_blanket_order()

        # Check if the blanket order is in "draft" state initially
        self.assertEqual(
            blanket_order.state, "draft", "Error: Blanket Order is not in draft state."
        )

        # Confirm the blanket order
        blanket_order.sudo().action_confirm()

        # Check if the state is updated to "Open" after confirmation
        self.assertEqual(
            blanket_order.state,
            "open",
            "Error: Blanket Order is not in open state after confirmation.",
        )

        # Check the order line (len)
        bo_lines = self.env["sale.blanket.order.line"].search(
            [("order_id", "=", blanket_order.id)]
        )

        self.assertEqual(len(bo_lines), 1)

        # Create a new wizard for the Blanket Order
        wizard = self._create_wizard(blanket_order)

        # Create sale order(s) using the wizard
        result = wizard.create_sale_order()

        sale_order_id = result.get("domain", [])[0][2][0]

        # Check if the state is updated to "Done" after processing
        self.assertEqual(
            blanket_order.state,
            "done",
            "Error: Blanket Order is not in done state after processing.",
        )

        # Search sale_order
        sale_order = self.env["sale.order"].search([("id", "=", sale_order_id)])

        # Check sale order state the wizard in draft
        self.assertEqual(
            sale_order.state,
            "draft",
            "Error: Sale Order is not in draft state.",
        )

        # Set the fiscal operation for each sale order line
        for order_line in sale_order.order_line:
            order_line.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
            order_line.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_venda_revenda"
            )

        # Confirm sale order using the wizard
        sale_order.action_confirm()

        # Check sale order state the wizard in sale
        self.assertEqual(
            sale_order.state,
            "sale",
            "Error: Sale Order is not in sale state after confirm.",
        )

        # Create invoice for the sale order
        invoices = {
            line.fiscal_operation_line_id.get_document_type(line.company_id)
            for line in sale_order.order_line
        }

        # Ensure there is at least one invoice created
        self.assertTrue(invoices, "Error: No invoices were created.")

        # Get the IDs of the invoices
        invoice_ids = [invoice.id for invoice in invoices]

        # Get the invoices related to the sale order
        invoices = self.env["account.move"].search([("id", "in", invoice_ids)])

        # Check if all invoices are in "draft" state initially
        self.assertTrue(
            all(invoice.state == "draft" for invoice in invoices),
            "Error: Not all invoices are in draft state after creation.",
        )

        # Validate the invoices
        for invoice in invoices:
            invoice.action_post()

        # Check if all invoices are in "posted" state after validation
        self.assertTrue(
            all(invoice.state == "posted" for invoice in invoices),
            "Error: Not all invoices are in posted state after validation.",
        )
