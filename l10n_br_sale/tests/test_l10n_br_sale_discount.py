# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command
from odoo.tests import Form, TransactionCase


class L10nBrSaleDiscount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.group_total_discount_id = cls.env.ref(
            "l10n_br_sale.group_total_discount"
        ).id
        cls.group_discount_per_value_id = cls.env.ref(
            "l10n_br_sale.group_discount_per_value"
        ).id
        cls.group_discount_per_so_line = cls.env.ref(
            "sale.group_discount_per_so_line"
        ).id
        sale_manager_user = cls.env.ref("sales_team.group_sale_manager")
        fiscal_user = cls.env.ref("l10n_br_fiscal.group_user")
        line_fiscal_detail = cls.env.ref("l10n_br_sale.group_line_fiscal_detail")
        user_groups = [sale_manager_user.id, fiscal_user.id, line_fiscal_detail.id]
        cls.user = (
            cls.env["res.users"]
            .with_user(cls.env.user)
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Test User",
                    "login": "test_user",
                    "email": "test@oca.com",
                    "company_id": cls.company.id,
                    "company_ids": [Command.link(cls.company.id)],
                    "groups_id": [Command.set(user_groups)],
                }
            )
        )

        cls.env = cls.env(user=cls.user)
        cls.cr = cls.env.cr

        cls.partner = cls.env["res.partner"].create({"name": "Test"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "test_product",
                "type": "service",
                "list_price": 1000,
            }
        )
        cls.order = Form(
            cls.env["sale.order"].with_context(
                default_company_id=cls.company.id,
            )
        )
        cls.order.partner_id = cls.partner
        cls.order = cls.order.save()

        cls.order_line = cls.env["sale.order.line"].create(
            {
                "name": cls.product.name,
                "product_id": cls.product.id,
                "product_uom_qty": 1,
                "product_uom": cls.product.uom_id.id,
                "price_unit": 1000.00,
                "order_id": cls.order.id,
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": cls.env.ref(
                    "l10n_br_fiscal.fo_venda_venda"
                ).id,
            },
        )

        cls.sales_view_id = "l10n_br_sale.l10n_br_sale_order_form"

    def _add_groups(self, *groups):
        """Add groups to the test user and invalidate caches that may hold
        stale group membership.

        In Odoo 18, two caches must be cleared:
        - The orm record cache for non-stored computed fields
          (user_discount_value, user_total_discount)
        - The ormcache on res.users._get_group_ids (used by has_group),
          which is a registry-level LRU cache keyed by user id
        """
        for group in groups:
            self.user.groups_id |= group
        self.order_line.invalidate_recordset(
            ["user_discount_value", "user_total_discount"]
        )
        self.env.registry.clear_all_caches()

    def test_l10n_br_sale_discount_value(self):
        """User with group_discount_per_value: discount_value drives discount."""
        self._add_groups(
            self.env.ref("l10n_br_sale.group_discount_per_value"),
            self.env.ref("sale.group_discount_per_so_line"),
        )

        line = self.order_line
        self.assertTrue(line.user_discount_value)
        self.assertFalse(line.user_total_discount)
        self.assertFalse(line.need_change_discount_value())

        # Setting discount_value computes discount via inverse
        line.discount_value = 450
        self.assertAlmostEqual(line.discount, 45.0)

        # Changing price_unit recomputes discount percentage from fixed value
        line.price_unit = 2000
        self.assertAlmostEqual(line.discount, 22.5)

        # need_change_discount_value() is False → discount is driven by
        # discount_value, so discount is effectively "readonly" in the UI
        # (the view modifier: user_discount_value or (...))

    def test_l10n_br_sale_discount_value_with_total(self):
        """User with value + total discount groups."""
        self._add_groups(
            self.env.ref("l10n_br_sale.group_discount_per_value"),
            self.env.ref("l10n_br_sale.group_total_discount"),
            self.env.ref("sale.group_discount_per_so_line"),
        )

        line = self.order_line
        self.assertTrue(line.user_discount_value)
        self.assertTrue(line.user_total_discount)
        self.assertTrue(line.need_change_discount_value())

        # Fix the line: need_change_discount_value becomes False
        line.discount_fixed = True
        self.assertFalse(line.need_change_discount_value())
        line.discount_fixed = False

        # With total discount and not fixed: discount_rate drives
        self.order.discount_rate = 10
        self.assertAlmostEqual(line.discount, 10.0)
        self.assertAlmostEqual(line.discount_value, 100.0)

        # Fix the line discount: discount_value drives
        line.discount_fixed = True
        line.discount_value = 450
        self.assertAlmostEqual(line.discount, 45.0)

        # Changing rate does not affect a fixed line
        self.order.discount_rate = 15
        self.assertAlmostEqual(line.discount, 45.0)
        self.assertAlmostEqual(line.discount_value, 450.0)

        # Unfix: follows rate again
        line.discount_fixed = False
        self.assertAlmostEqual(line.discount, 15.0)
        self.assertAlmostEqual(line.discount_value, 150.0)

    def test_l10n_br_sale_discount_percent(self):
        """User with only percent discount (no value group).

        In Odoo 18, discount_value is not visible in the Form view when the
        user lacks group_discount_per_value, so we test via direct record
        operations instead of the Form.
        """
        # Initially user has neither value nor total discount group
        self.assertFalse(self.order_line.user_discount_value)
        self.assertFalse(self.order_line.user_total_discount)
        self.assertTrue(self.order_line.need_change_discount_value())

        self._add_groups(self.env.ref("sale.group_discount_per_so_line"))

        line = self.order_line
        # Setting discount computes discount_value via inverse
        line.discount = 33
        self.assertAlmostEqual(line.discount_value, 330.0)

        # Changing price_unit recomputes discount_value from percentage
        line.price_unit = 2000
        self.assertAlmostEqual(line.discount_value, 660.0)

    def test_l10n_br_sale_discount_percent_with_total(self):
        """User with total discount but not value discount."""
        self._add_groups(
            self.env.ref("l10n_br_sale.group_total_discount"),
            self.env.ref("sale.group_discount_per_so_line"),
        )

        line = self.order_line
        self.assertFalse(line.user_discount_value)
        self.assertTrue(line.user_total_discount)
        self.assertTrue(line.need_change_discount_value())

        # Even with discount_fixed=True, need_change_discount_value is True
        # because user_discount_value is False
        line.discount_fixed = True
        self.assertTrue(line.need_change_discount_value())
        line.discount_fixed = False

        # With total discount and not fixed: discount_rate drives
        self.order.discount_rate = 15
        self.assertAlmostEqual(line.discount, 15.0)
        self.assertAlmostEqual(line.discount_value, 150.0)

        # Fix the line: discount percent drives
        line.discount_fixed = True
        line.discount = 50
        self.assertAlmostEqual(line.discount_value, 500.0)

        # Changing rate does not affect a fixed line
        self.order.discount_rate = 35
        self.assertAlmostEqual(line.discount, 50.0)
        self.assertAlmostEqual(line.discount_value, 500.0)

        # Unfix: follows rate again
        line.discount_fixed = False
        self.assertAlmostEqual(line.discount, 35.0)
        self.assertAlmostEqual(line.discount_value, 350.0)
