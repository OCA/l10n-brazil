# Copyright 2020, KMEE - kmee.com.br - Diego Paradeda <diego.paradeda@kmee.com.br>
# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestUi(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("website.default_website")
        cls.currency = cls.env.ref("base.BRL")
        cls.currency.active = True
        cls.city = cls.env.ref("l10n_br_base.city_3549904")
        cls.company = cls.env["res.company"].create(
            {
                "name": "Freight Test Brazil",
                "currency_id": cls.currency.id,
                "country_id": cls.city.country_id.id,
                "state_id": cls.city.state_id.id,
                "city_id": cls.city.id,
            }
        )
        cls.website.company_id = cls.company
        cls.env["product.pricelist"].create(
            {
                "name": "Freight Test BRL",
                "currency_id": cls.currency.id,
                "company_id": cls.company.id,
                "website_id": cls.website.id,
                "sequence": 0,
            }
        )
        cls.company.delivery_costs = "line"
        cls.company.sale_fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.website.account_on_checkout = "optional"
        cls.website.viewref("website_sale.address_b2b").active = False
        cls.website.user_id.partner_id.country_id = False
        cls.product = cls.env["product.template"].create(
            {
                "name": "Freight Test Storage Box",
                "detailed_type": "consu",
                "list_price": 100,
                "taxes_id": [Command.clear()],
                "website_published": True,
                "company_id": cls.company.id,
            }
        )
        cls.free_carrier = cls._create_carrier("Freight Test Free", 0)
        cls.paid_carrier = cls._create_carrier("Freight Test Poste", 20)

    @classmethod
    def _create_carrier(cls, name, price):
        product = cls.env["product.product"].create(
            {
                "name": name,
                "detailed_type": "service",
                "sale_ok": False,
                "purchase_ok": False,
                "list_price": price,
                "taxes_id": [Command.clear()],
                "company_id": cls.company.id,
            }
        )
        return cls.env["delivery.carrier"].create(
            {
                "name": name,
                "delivery_type": "fixed",
                "product_id": product.id,
                "website_published": True,
                "company_id": cls.company.id,
            }
        )

    def test_freight_checkout(self):
        with patch(
            "odoo.addons.l10n_br_zip.models.l10n_br_zip.get_address_from_cep",
            return_value={
                "street": "Rua do Aruana",
                "district": "Parque Residencial Aquarius",
                "city": self.city.name,
                "uf": self.city.state_id.code,
                "complement": "",
            },
        ) as cep:
            self.start_tour(
                self.product.website_url, "l10n_br_website_sale_delivery_tour"
            )
        self.assertTrue(cep.called)
        order = self.env["sale.order"].search(
            [
                ("website_id", "=", self.website.id),
                ("partner_id.email", "=", "freight-checkout@example.com"),
                ("order_line.product_id", "=", self.product.product_variant_id.id),
            ]
        )
        self.assertEqual(len(order), 1)
        self.assertEqual(order.partner_shipping_id.city_id, self.city)
        self.assertEqual(order.currency_id, self.currency)
        self.assertTrue(order.force_compute_delivery_costs_by_total)
        self.assertEqual(self.company.delivery_costs, "line")
        self.assertEqual(order.carrier_id, self.paid_carrier)
        lines = order.order_line
        self.assertFalse(lines.filtered("is_delivery"))
        self.assertEqual(lines.product_uom_qty, 2)
        self.assertEqual(self.currency.compare_amounts(lines.freight_value, 20), 0)
        self.assertEqual(
            self.currency.compare_amounts(order.amount_freight_value, 20), 0
        )
        self.assertEqual(self.currency.compare_amounts(order.amount_delivery, 20), 0)
        self.assertEqual(self.currency.compare_amounts(order.amount_total, 220), 0)
        order.action_confirm()
        self.assertEqual(order.state, "sale")
        self.assertEqual(
            self.currency.compare_amounts(order.amount_freight_value, 20), 0
        )

    def test_create_website_and_backend_orders_together(self):
        partner = self.env["res.partner"].create({"name": "Freight Test Customer"})
        order_model = self.env["sale.order"]
        values = {"partner_id": partner.id, "company_id": self.company.id}
        backend, website = order_model.create(
            [values, dict(values, website_id=self.website.id)]
        )
        self.assertFalse(backend.force_compute_delivery_costs_by_total)
        self.assertTrue(website.force_compute_delivery_costs_by_total)
        website, backend = order_model.with_context(
            default_website_id=self.website.id
        ).create([values, dict(values, website_id=False)])
        self.assertTrue(website.force_compute_delivery_costs_by_total)
        self.assertFalse(backend.force_compute_delivery_costs_by_total)
