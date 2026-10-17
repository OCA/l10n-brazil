# Copyright 2023 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class L10nBrSaleBLanketOrderTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                allowed_company_ids=cls.company.ids,
            )
        )

        # BR fiscal demo partner: maps ICMS + icms_cst_id so invoice posting can
        # serialize NF-e when CI has l10n_br_nfe installed.
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.payment_term = cls.env.ref("account.account_payment_term_immediate")
        cls.pricelist = cls.env.ref("product.list0")
        cls.validity_date = date.today() + timedelta(days=2)
        cls.cnae_secondary = cls.env.ref("l10n_br_fiscal.cnae_31021")

        cls.product = cls.env.ref("product.product_product_27")
        cls.product_uom = cls.env.ref("uom.product_uom_unit")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fiscal_operation_line_revenda = cls.env.ref(
            "l10n_br_fiscal.fo_venda_revenda"
        )
        cls.icms_cst_00 = cls.env.ref("l10n_br_fiscal.cst_icms_00")

        cls.company.cnae_secondary_ids = [(6, 0, [cls.cnae_secondary.id])]

    # Helper method to create a new Blanket Order for testing.
    def _create_blanket_order(self):
        values = {
            "partner_id": self.partner.id,
            "company_id": self.company.id,
            "validity_date": self.validity_date,
            "payment_term_id": self.payment_term.id,
            "pricelist_id": self.pricelist.id,
            "fiscal_operation_id": self.fiscal_operation.id,
            "line_ids": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "product_uom": self.product_uom.id,
                        "original_uom_qty": 20.0,
                        "price_unit": 25.0,
                        "fiscal_operation_id": self.fiscal_operation.id,
                    }
                )
            ],
        }
        # Create new register blanket.order
        blanket_order = (
            self.env["sale.blanket.order"].with_company(self.company).create(values)
        )
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
        bo_line = bo_lines[0]
        self.assertTrue(
            bo_line.fiscal_operation_line_id,
            "Error: Blanket Order line has no fiscal operation line.",
        )
        self.assertTrue(
            bo_line.fiscal_tax_ids,
            "Error: Blanket Order line has no fiscal taxes.",
        )
        expected_account_taxes = bo_line.fiscal_tax_ids.account_taxes(
            user_type="sale",
            fiscal_operation=bo_line.fiscal_operation_id,
            company=bo_line.company_id,
        )
        self.assertTrue(
            bo_line.taxes_id,
            "Error: Blanket Order line taxes_id was not filled from fiscal taxes.",
        )
        self.assertEqual(bo_line.taxes_id, expected_account_taxes)

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

        for order_line in sale_order.order_line:
            self.assertTrue(
                order_line.fiscal_operation_line_id,
                "Error: Sale Order line has no fiscal operation line.",
            )
            self.assertTrue(
                order_line.tax_id,
                "Error: Sale Order line tax_id was not filled from blanket taxes.",
            )
            self.assertEqual(order_line.tax_id, expected_account_taxes)
            # Classic revenda + fiscal tax onchange keeps ICMS CST for NF-e
            # serialization when l10n_br_nfe is installed in CI.
            order_line.fiscal_operation_line_id = self.fiscal_operation_line_revenda
            order_line._onchange_fiscal_taxes()
            if not order_line.icms_cst_id:
                order_line.icms_cst_id = self.icms_cst_00

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

        # Ensure ICMS CST before post: nfe40_choice_icms is computed from it and
        # l10n_br_nfe export crashes when the selection stays False.
        for invoice in invoices:
            for line in invoice.invoice_line_ids.filtered(
                lambda aml: aml.display_type == "product" and not aml.icms_cst_id
            ):
                line.icms_cst_id = self.icms_cst_00
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
        self.assertTrue(bo_line.fiscal_operation_line_id)
        self.assertTrue(bo_line.taxes_id)

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

    def test_onchange_product_keeps_taxes_id_from_fiscal(self):
        """Inline tree product onchange must not leave taxes_id empty on BR CoA.

        OCA onchange_product sets taxes_id from product.taxes_id (usually empty);
        the BR override re-syncs from fiscal_tax_ids afterwards.
        """
        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        line = blanket_order.line_ids[0]
        self.assertTrue(line.fiscal_tax_ids)

        # Simulate the OCA onchange wiping taxes_id, then BR re-sync.
        line.taxes_id = False
        line.onchange_product()
        expected = line.fiscal_tax_ids.account_taxes(
            user_type="sale",
            fiscal_operation=line.fiscal_operation_id,
            company=line.company_id or line.order_id.company_id,
        )
        self.assertTrue(line.taxes_id)
        self.assertEqual(line.taxes_id, expected)

        line._onchange_fiscal_tax_ids()
        self.assertEqual(line.taxes_id, expected)

    def test_withholding_tax_keeps_fiscal_totals(self):
        """Adding a withholding tax must keep totals after form save.

        The line form onchange computes amount_tax_withholding correctly, but
        saving sends fiscal_tax_ids together with *_tax_id. That write used to
        recompute taxes on stale values and persist withholding=0.
        """
        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        line = blanket_order.line_ids[0]
        line.write({"original_uom_qty": 1.0, "price_unit": 100.0})

        inss_wh = self.env["l10n_br_fiscal.tax"].search(
            [("tax_domain", "=", "inss_wh")], limit=1
        )
        if not inss_wh:
            self.skipTest("No inss_wh fiscal tax found in demo data.")

        # Reproduce UI save: both fiscal_tax_ids and the specific tax field.
        taxes = line.fiscal_tax_ids | inss_wh
        line.write(
            {
                "inss_wh_tax_id": inss_wh.id,
                "fiscal_tax_ids": [Command.set(taxes.ids)],
            }
        )
        line.invalidate_recordset()

        self.assertAlmostEqual(line.price_gross, 100.0, places=2)
        self.assertAlmostEqual(line.amount_fiscal, 100.0, places=2)
        self.assertAlmostEqual(line.fiscal_amount_untaxed, 100.0, places=2)
        self.assertTrue(
            line.amount_tax_withholding,
            "amount_tax_withholding must persist after saving fiscal taxes.",
        )
        self.assertAlmostEqual(
            line.fiscal_amount_total,
            line.fiscal_amount_untaxed
            + line.fiscal_amount_tax
            - line.amount_tax_withholding,
            places=2,
        )

    def test_cnae_domain(self):
        domain = self.env["sale.blanket.order.line"]._cnae_domain()
        expected_domain = [
            "|",
            ("id", "in", [self.cnae_secondary.id]),
            ("id", "=", self.company.cnae_main_id.id),
        ]
        self.assertEqual(domain, expected_domain)

    def test_cnae_domain_without_secondary_cnae(self):
        secondary_cnae_ids = self.company.cnae_secondary_ids.ids
        try:
            self.company.cnae_secondary_ids = [Command.clear()]
            domain = self.env["sale.blanket.order.line"]._cnae_domain()
            self.assertEqual(domain, [])
        finally:
            self.company.cnae_secondary_ids = [Command.set(secondary_cnae_ids)]

    def test_compute_price_unit_fiscal(self):
        blanket_order = self._create_blanket_order()
        blanket_line = blanket_order.line_ids

        # sale_price uses pricelist / tax-included unit price.
        self.assertEqual(
            blanket_line.fiscal_operation_id.default_price_unit, "sale_price"
        )
        expected_sale_price = self.product._get_tax_included_unit_price(
            blanket_line.company_id,
            blanket_order.currency_id,
            blanket_order.validity_date,
            "sale",
            fiscal_position=blanket_order.fiscal_position_id,
            product_price_unit=blanket_line._get_display_price(blanket_line.product_id),
            product_currency=blanket_order.currency_id,
        )
        blanket_line._compute_price_unit_fiscal()
        self.assertEqual(blanket_line.price_unit, expected_sale_price)

        # cost_price falls back to standard_price.
        fo_compras = self.env.ref("l10n_br_fiscal.fo_compras")
        self.assertEqual(fo_compras.default_price_unit, "cost_price")
        blanket_line.fiscal_operation_id = fo_compras
        blanket_line._compute_price_unit_fiscal()
        self.assertEqual(blanket_line.price_unit, self.product.standard_price)

        # Unknown / empty default_price_unit zeroes the unit price.
        blanket_line.fiscal_operation_id = False
        blanket_line._compute_price_unit_fiscal()
        self.assertEqual(blanket_line.price_unit, 0.0)

    def test_prepare_so_vals_rejects_different_fiscal_operations(self):
        blanket_order = self._create_blanket_order()
        wizard = self._create_wizard(blanket_order)
        blanket_line = blanket_order.line_ids
        customer = self.partner.id
        order_lines_by_customer = {
            customer: [
                (
                    0,
                    0,
                    {
                        "fiscal_operation_id": self.fiscal_operation.id,
                        "blanket_order_line": blanket_line.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "fiscal_operation_id": self.env.ref(
                            "l10n_br_fiscal.fo_compras"
                        ).id,
                        "blanket_order_line": blanket_line.id,
                    },
                ),
            ]
        }

        with self.assertRaises(UserError):
            wizard._prepare_so_vals(
                customer=customer,
                user_id=self.env.user.id,
                currency_id=blanket_order.currency_id.id,
                pricelist_id=blanket_order.pricelist_id.id,
                payment_term_id=blanket_order.payment_term_id.id,
                client_order_ref=False,
                tag_ids=False,
                order_lines_by_customer=order_lines_by_customer,
            )

    def test_prepare_so_line_forces_tax_id_from_fiscal(self):
        """Wizard must fill SO tax_id even when blanket taxes_id is empty."""
        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        blanket_order.sudo().action_confirm()
        bo_line = blanket_order.line_ids[0]
        self.assertTrue(bo_line.fiscal_tax_ids)

        # Simulate stale/empty commercial taxes on the blanket line.
        bo_line.taxes_id = False
        expected = bo_line.fiscal_tax_ids.account_taxes(
            user_type="sale",
            fiscal_operation=bo_line.fiscal_operation_id,
            company=bo_line.company_id or blanket_order.company_id,
        )
        self.assertTrue(expected)

        wizard = self._create_wizard(blanket_order)
        vals = wizard._prepare_so_line_vals(wizard.line_ids)
        self.assertEqual(vals["tax_id"], [Command.set(expected.ids)])
        self.assertEqual(vals["company_id"], blanket_order.company_id.id)

    def test_withholding_tax_persists_on_create(self):
        """Creating a line with fiscal_tax_ids + *_tax_id must keep withholding."""
        inss_wh = self.env["l10n_br_fiscal.tax"].search(
            [("tax_domain", "=", "inss_wh")], limit=1
        )
        if not inss_wh:
            self.skipTest("No inss_wh fiscal tax found in demo data.")

        blanket_order = self._create_blanket_order()
        blanket_order._onchange_fiscal_operation_id()
        template = blanket_order.line_ids[0]
        taxes = template.fiscal_tax_ids | inss_wh

        line = self.env["sale.blanket.order.line"].create(
            {
                "order_id": blanket_order.id,
                "product_id": self.product.id,
                "product_uom": self.product_uom.id,
                "original_uom_qty": 1.0,
                "price_unit": 100.0,
                "fiscal_operation_id": self.fiscal_operation.id,
                "fiscal_operation_line_id": template.fiscal_operation_line_id.id,
                "fiscal_tax_ids": [Command.set(taxes.ids)],
                "inss_wh_tax_id": inss_wh.id,
            }
        )
        line.invalidate_recordset()

        self.assertAlmostEqual(line.price_gross, 100.0, places=2)
        self.assertTrue(
            line.amount_tax_withholding,
            "amount_tax_withholding must persist after create with fiscal taxes.",
        )
        self.assertAlmostEqual(
            line.fiscal_amount_total,
            line.fiscal_amount_untaxed
            + line.fiscal_amount_tax
            - line.amount_tax_withholding,
            places=2,
        )

    def test_get_document(self):
        blanket_order = self._create_blanket_order()
        line = blanket_order.line_ids[0]
        self.assertEqual(line._get_document(), blanket_order)

    def test_get_view(self):
        """Covers all _get_view branches for sale.blanket.order."""

        sale_blanket_order = self.env["sale.blanket.order"]
        group_fiscal = self.env.ref(
            "l10n_br_sale.group_line_fiscal_detail", raise_if_not_found=False
        ) or self.skipTest("Group l10n_br_sale.group_line_fiscal_detail not found.")

        with self.subTest("BR company - form view - fiscal fields injected"):
            arch, _ = sale_blanket_order._get_view(view_type="form")
            injected = {el.get("name") for el in arch.findall(".//field")}
            self.assertIn("fiscal_operation_id", injected)
            self.assertIn("icms_tax_id", injected)
            # C4 census "dead" fiscal computes are pruned from the injection
            for dead in (
                "ii_percent",
                "simple_value",
                "simple_without_icms_value",
                "cofins_wh_base_type",
                "pis_wh_base_type",
            ):
                self.assertNotIn(dead, injected)

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
