# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import Form, TransactionCase


class L10nBrSaleDiscount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.group_total_discount_id = cls.env.ref(
            "l10n_br_sale.group_total_discount"
        ).id
        cls.group_discount_per_value_id = cls.env.ref(
            "l10n_br_sale.group_discount_per_value"
        ).id
        cls.group_discount_per_so_line = cls.env.ref(
            "product.group_discount_per_so_line"
        ).id
        sale_manager_user = cls.env.ref("sales_team.group_sale_manager")
        fiscal_user = cls.env.ref("l10n_br_fiscal.group_user")
        user_groups = [sale_manager_user.id, fiscal_user.id]
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
                    "company_ids": [(4, cls.company.id)],
                    "groups_id": [(6, 0, user_groups)],
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
        cls.order = Form(cls.env["sale.order"])
        cls.order.partner_id = cls.partner
        cls.order.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
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

    def test_l10n_br_sale_discount_value(self):
        self.user.groups_id = [(4, self.group_discount_per_value_id)]
        self.user.groups_id = [(4, self.group_discount_per_so_line)]

        self.assertTrue(self.order_line.user_discount_value)
        self.assertFalse(self.order_line.user_total_discount)
        self.assertFalse(self.order_line.need_change_discount_value())

        order = Form(self.order)
        with order.order_line.edit(0) as line:
            line.discount_value = 450
            self.assertEqual(line.discount, 45)
            line.price_unit = 2000
            self.assertEqual(line.discount, 22.5)
            with self.assertRaises(AssertionError):
                line.discount = 20

    def test_l10n_br_sale_discount_value_with_total(self):
        self.user.groups_id = [(4, self.group_discount_per_value_id)]
        self.user.groups_id = [(4, self.group_total_discount_id)]
        self.user.groups_id = [(4, self.group_discount_per_so_line)]

        self.assertTrue(self.order_line.user_discount_value)
        self.assertTrue(self.order_line.user_total_discount)
        self.assertTrue(self.order_line.need_change_discount_value())
        self.order_line.discount_fixed = True
        self.assertFalse(self.order_line.need_change_discount_value())
        self.order_line.discount_fixed = False

        order = Form(self.order)
        order.discount_rate = 10
        with order.order_line.edit(0) as line:
            self.assertEqual(line.discount, 10)
            self.assertEqual(line.discount_value, 100)
            with self.assertRaises(AssertionError):
                line.discount = 20
            with self.assertRaises(AssertionError):
                line.discount_value = 20
            line.discount_fixed = True
            line.discount_value = 450
            self.assertEqual(line.discount, 45)
            with self.assertRaises(AssertionError):
                line.discount = 20
        order.discount_rate = 15
        with order.order_line.edit(0) as line:
            self.assertEqual(line.discount, 45)
            self.assertEqual(line.discount_value, 450)
            line.discount_fixed = False
            self.assertEqual(line.discount, 15)
            self.assertEqual(line.discount_value, 150)

    def test_l10n_br_sale_discount_percent(self):
        self.assertFalse(self.order_line.user_discount_value)
        self.assertFalse(self.order_line.user_total_discount)
        self.assertTrue(self.order_line.need_change_discount_value())

        self.user.groups_id = [(4, self.group_discount_per_so_line)]
        order = Form(self.order)
        with order.order_line.edit(0) as line:
            line.discount = 33
            self.assertEqual(line.discount_value, 330)
            line.price_unit = 2000
            self.assertEqual(line.discount_value, 660)
            with self.assertRaises(AssertionError):
                line.discount_value = 20

    def test_l10n_br_sale_discount_percent_with_total(self):
        self.user.groups_id = [(4, self.group_total_discount_id)]
        self.user.groups_id = [(4, self.group_discount_per_so_line)]

        self.assertFalse(self.order_line.user_discount_value)
        self.assertTrue(self.order_line.user_total_discount)
        self.assertTrue(self.order_line.need_change_discount_value())
        self.order_line.discount_fixed = True
        self.assertTrue(self.order_line.need_change_discount_value())
        self.order_line.discount_fixed = False

        order = Form(self.order)
        order.discount_rate = 15
        with order.order_line.edit(0) as line:
            self.assertEqual(line.discount, 15)
            self.assertEqual(line.discount_value, 150)
            with self.assertRaises(AssertionError):
                line.discount = 20
            with self.assertRaises(AssertionError):
                line.discount_value = 20
            line.discount_fixed = True
            line.discount = 50
            self.assertEqual(line.discount_value, 500)
            with self.assertRaises(AssertionError):
                line.discount_value = 20
        order.discount_rate = 35
        with order.order_line.edit(0) as line:
            self.assertEqual(line.discount, 50)
            self.assertEqual(line.discount_value, 500)
            line.discount_fixed = False
            self.assertEqual(line.discount, 35)
            self.assertEqual(line.discount_value, 350)
