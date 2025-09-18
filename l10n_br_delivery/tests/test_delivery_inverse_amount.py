# @ 2020 KMEE - www.kmee.com.br
# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import Form, TransactionCase


class TestDeliveryInverseAmount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.user.company_id
        cls.partner = cls.env.ref("l10n_br_base.res_partner_kmee")
        cls.product1 = cls.env.ref("product.product_delivery_01")  # Price: 70.0
        cls.product2 = cls.env.ref("product.product_delivery_02")  # Price: 40.0

    def _create_and_prepare_so(self):
        """Helper to create a draft SO with two lines."""
        so_form = Form(self.env["sale.order"])
        so_form.partner_id = self.partner
        with so_form.order_line.new() as line:
            line.product_id = self.product1
            line.product_uom_qty = 1.0
        with so_form.order_line.new() as line:
            line.product_id = self.product2
            line.product_uom_qty = 1.0
        return so_form.save()

    def _process_so_to_invoice(self, sale_order):
        """Helper to confirm an SO, process its picking, and create an invoice."""
        sale_order.action_confirm()

        picking = sale_order.picking_ids
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

        wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(active_ids=sale_order.ids)
            .create({})
        )
        wizard.create_invoices()
        return sale_order.invoice_ids

    def test_delivery_costs_by_line(self):
        """
        Tests when costs are entered on each SO line. The invoice should reflect
        these exact line values.
        """
        self.company.delivery_costs = "line"
        so = self._create_and_prepare_so()

        # Update SO lines with costs
        with Form(so) as so_form:
            with so_form.order_line.edit(0) as line:
                line.freight_value = 70.00
                line.insurance_value = 60.00
                line.other_value = 50.00
            with so_form.order_line.edit(1) as line:
                line.freight_value = 10.00
                line.insurance_value = 20.00
                line.other_value = 30.00

        # Check SO header totals are summed correctly
        self.assertAlmostEqual(so.amount_freight_value, 80.0)
        self.assertAlmostEqual(so.amount_insurance_value, 80.0)
        self.assertAlmostEqual(so.amount_other_value, 80.0)

        # Create the invoice from the finalized SO
        invoice = self._process_so_to_invoice(so)
        fiscal_document = invoice.fiscal_document_id

        # Check invoice header totals
        self.assertAlmostEqual(fiscal_document.amount_freight_value, 80.0)
        self.assertAlmostEqual(fiscal_document.amount_insurance_value, 80.0)
        self.assertAlmostEqual(fiscal_document.amount_other_value, 80.0)

        # Check invoice line values (should match SO line values)
        line1 = fiscal_document.fiscal_line_ids.filtered(
            lambda line: line.product_id == self.product1
        )
        line2 = fiscal_document.fiscal_line_ids.filtered(
            lambda line: line.product_id == self.product2
        )
        self.assertAlmostEqual(line1.freight_value, 70.0)
        self.assertAlmostEqual(line2.freight_value, 10.0)
        self.assertAlmostEqual(line1.insurance_value, 60.0)
        self.assertAlmostEqual(line2.insurance_value, 20.0)
        self.assertAlmostEqual(line1.other_value, 50.0)
        self.assertAlmostEqual(line2.other_value, 30.0)

    def test_delivery_costs_by_total(self):
        """
        Tests when costs are entered on the SO header. The invoice should reflect
        these header values and distribute them proportionally to the lines
        based on price_gross.
        """
        self.company.delivery_costs = "total"
        so = self._create_and_prepare_so()

        # Update SO header with total costs
        with Form(so) as so_form:
            so_form.amount_freight_value = 100.0
            so_form.amount_insurance_value = 100.0
            so_form.amount_other_value = 100.0

        # Create the invoice from the finalized SO
        invoice = self._process_so_to_invoice(so)
        fiscal_document = invoice.fiscal_document_id

        # Proportionality check:
        # line1 price_gross = 1 * 70 = 70
        # line2 price_gross = 1 * 40 = 40
        # total_gross = 110
        # line1 proportion = 70 / 110
        # line2 proportion = 40 / 110

        # Check invoice header totals
        self.assertAlmostEqual(fiscal_document.amount_freight_value, 100.0)
        self.assertAlmostEqual(fiscal_document.amount_insurance_value, 100.0)
        self.assertAlmostEqual(fiscal_document.amount_other_value, 100.0)

        # Check invoice line values (should be proportionally distributed)
        line1 = fiscal_document.fiscal_line_ids.filtered(
            lambda line: line.product_id == self.product1
        )
        line2 = fiscal_document.fiscal_line_ids.filtered(
            lambda line: line.product_id == self.product2
        )

        self.assertAlmostEqual(line1.freight_value, 100.0 * (70.0 / 110.0), 2)
        self.assertAlmostEqual(line2.freight_value, 100.0 * (40.0 / 110.0), 2)

        self.assertAlmostEqual(line1.insurance_value, 100.0 * (70.0 / 110.0), 2)
        self.assertAlmostEqual(line2.insurance_value, 100.0 * (40.0 / 110.0), 2)

        self.assertAlmostEqual(line1.other_value, 100.0 * (70.0 / 110.0), 2)
        self.assertAlmostEqual(line2.other_value, 100.0 * (40.0 / 110.0), 2)
