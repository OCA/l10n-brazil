# Copyright 2023 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from datetime import date, timedelta

from lxml import etree

from odoo.fields import Command
from odoo.tests.common import TransactionCase


class L10nBrSaleBLanketOrderTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Set up some test data like partner, payment term, company, pricelist, etc.
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.payment_term = cls.env.ref("account.account_payment_term_immediate")
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.pricelist = cls.env.ref("product.list0")
        cls.validity_date = date.today() + timedelta(days=2)
        cls.cnae_secondary = cls.env.ref("l10n_br_fiscal.cnae_31021")

        cls.product = cls.env.ref("product.product_product_27")
        cls.product_uom = cls.env.ref("uom.product_uom_unit")

        cls.company.cnae_secondary_ids = [(6, 0, [cls.cnae_secondary.id])]
        cls.env.company = cls.company

    # Helper method to create a new Blanket Order for testing.
    def _create_blanket_order(self):
        values = {
            "partner_id": self.partner.id,
            "validity_date": self.validity_date,
            "payment_term_id": self.payment_term.id,
            "pricelist_id": self.pricelist.id,
            "line_ids": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "product_uom": self.product_uom.id,
                        "original_uom_qty": 20.0,
                        "price_unit": 25.0,
                    }
                )
            ],
        }
        # Create new register blanket.order
        blanket_order = self.env["sale.blanket.order"].create(values)
        blanket_order.sudo().onchange_partner_id()

        return blanket_order

    # Helper method to create a new wizard for testing, based on a Blanket Order.
    def _create_wizard(self, blanket_order):
        lines = [
            Command.create(
                {
                    "blanket_line_id": line.id,
                    "product_id": line.product_id.id,
                    "date_schedule": line.date_schedule,
                    "remaining_uom_qty": line.remaining_uom_qty,
                    "price_unit": line.price_unit,
                    "product_uom": line.product_uom,
                    "qty": line.remaining_uom_qty,
                    "partner_id": line.partner_id.id,
                }
            )
            for line in blanket_order.line_ids
        ]

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

    @contextmanager
    def _temporary_company_country(self, country):
        original_country = self.company.country_id
        self.company.country_id = country
        try:
            yield
        finally:
            self.company.country_id = original_country

    @contextmanager
    def _temporary_user_groups(self, groups):
        original_groups = self.env.user.groups_id
        self.env.user.groups_id = groups
        try:
            yield
        finally:
            self.env.user.groups_id = original_groups

    # Test method to confirm and process a Blanket Order.
    def test_confirm_and_process_blanket_order_and_invoice(self):
        # Create a new Blanket Order for testing
        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        blanket_order._amount_all()

        # Check if the blanket order is in "draft" state initially
        self.assertEqual(
            blanket_order.state, "draft", "Error: Blanket Order is not in draft state."
        )
        self.assertEqual(blanket_order.fiscal_operation_id.code, "VD")
        self.assertEqual(blanket_order.fiscal_operation_id.fiscal_type, "sale")

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

        invoice_wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(active_ids=sale_order.ids, active_model="sale.order")
            .create(
                {
                    "advance_payment_method": "delivered",
                }
            )
        )

        invoice_wizard.create_invoices()

        invoices = sale_order.invoice_ids
        self.assertTrue(invoices)

        for invoice in invoices:
            self.assertEqual(
                invoice.fiscal_operation_id,
                sale_order.order_line[0].fiscal_operation_id,
            )

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

    def test_partial_quantity_recomputes_fiscal_amounts(self):
        """A sale order created from a blanket order line for a partial
        quantity must have its fiscal amounts recomputed for that quantity,
        not copied over from the blanket order line's original quantity.
        """
        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        blanket_order._amount_all()
        blanket_order.sudo().action_confirm()

        bo_line = blanket_order.line_ids[0]
        self.assertEqual(bo_line.quantity, 20.0)
        bo_line.write(
            {
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_venda_revenda"
                ).id,
            }
        )

        full_price_subtotal = bo_line.price_subtotal
        self.assertTrue(full_price_subtotal)
        partial_qty = 5.0
        wizard = (
            self.env["sale.blanket.order.wizard"]
            .with_context(active_id=blanket_order.id, active_model="sale.blanket.order")
            .create(
                {
                    "blanket_order_id": blanket_order.id,
                    "line_ids": [
                        Command.create(
                            {
                                "blanket_line_id": bo_line.id,
                                "product_id": bo_line.product_id.id,
                                "date_schedule": bo_line.date_schedule,
                                "remaining_uom_qty": bo_line.remaining_uom_qty,
                                "price_unit": bo_line.price_unit,
                                "product_uom": bo_line.product_uom,
                                "qty": partial_qty,
                                "partner_id": bo_line.partner_id.id,
                            }
                        )
                    ],
                }
            )
        )

        result = wizard.create_sale_order()
        sale_order = self.env["sale.order"].browse(result["domain"][0][2][0])
        so_line = sale_order.order_line[0]
        self.assertEqual(so_line.product_uom_qty, partial_qty)
        expected_subtotal = full_price_subtotal * partial_qty / bo_line.quantity
        self.assertAlmostEqual(so_line.price_subtotal, expected_subtotal, 2)
        self.assertNotAlmostEqual(so_line.price_subtotal, full_price_subtotal, 2)

    def test_cnae_domain(self):
        domain = self.env["sale.blanket.order.line"]._cnae_domain()
        expected_domain = [
            "|",
            ("id", "in", [self.cnae_secondary.id]),
            ("id", "=", self.company.cnae_main_id.id),
        ]
        self.assertEqual(domain, expected_domain)

    def test_get_view(self):
        """Covers all _get_view branches for sale.blanket.order."""

        sale_blanket_order = self.env["sale.blanket.order"]
        group_fiscal = self.env.ref(
            "l10n_br_sale.group_line_fiscal_detail", raise_if_not_found=False
        ) or self.skipTest("Group l10n_br_sale.group_line_fiscal_detail not found.")

        with self.subTest("BR company - form view - fiscal fields injected"):
            arch, _ = sale_blanket_order._get_view(view_type="form")
            self.assertIn(
                "fiscal_operation_id", etree.tostring(arch, encoding="unicode")
            )

        with self.subTest("Non-BR company - form view - line_ids tree not modified"):
            us_country = self.env.ref("base.us")
            with self._temporary_company_country(us_country):
                arch_non_br, _ = sale_blanket_order._get_view(view_type="form")
                self.assertFalse(
                    any(
                        sub_tree.get("editable") == ""
                        for sub_tree in arch_non_br.xpath(
                            "//field[@name='line_ids']/tree"
                        )
                    ),
                    "Error: line_ids tree should not be editable for non-BR company.",
                )

        with self.subTest("BR company - fiscal group - line_ids tree editable"):
            with self._temporary_user_groups([(4, group_fiscal.id)]):
                arch_group, _ = sale_blanket_order._get_view(view_type="form")
                self.assertTrue(
                    all(
                        sub_tree.get("editable", "NOT_SET") == ""
                        for sub_tree in arch_group.xpath(
                            "//field[@name='line_ids']/tree"
                        )
                    ),
                    "Error: line_ids tree should be editable for fiscal detail group.",
                )

        with self.subTest("BR company - force_line_fiscal_detail_edition context"):
            arch_ctx, _ = sale_blanket_order.with_context(
                force_line_fiscal_detail_edition=True
            )._get_view(view_type="form")
            self.assertTrue(
                all(
                    sub_tree.get("editable", "NOT_SET") == ""
                    for sub_tree in arch_ctx.xpath("//field[@name='line_ids']/tree")
                ),
                "Error: line_ids tree editable with force_line_fiscal_detail_edition.",
            )
