# @ 2020 KMEE - kmee.com.br
#   Diego Paradeda <diego.paradeda@kme.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from unittest.mock import patch

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestUi(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env.ref("website.default_website")
        cls.city = cls.env.ref("l10n_br_base.city_3500105")
        cls.website.company_id.partner_id.write(
            {
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.city.state_id.id,
                "city_id": cls.city.id,
            }
        )
        cls.website.account_on_checkout = "optional"
        cls.website.viewref("website_sale.address_b2b").active = False
        cls.website.user_id.partner_id.country_id = False
        cls.product = cls.env["product.template"].create(
            {
                "name": "Checkout Test Service",
                "type": "service",
                "list_price": 20,
                "website_published": True,
            }
        )

    def _get_checkout_order(self, email):
        order = self.env["sale.order"].search(
            [
                ("website_id", "=", self.website.id),
                ("partner_id.email", "=", email),
                ("order_line.product_id", "=", self.product.product_variant_id.id),
            ]
        )
        self.assertEqual(len(order), 1)
        return order

    def test_brazilian_checkout(self):
        operation = self.env.ref("l10n_br_fiscal.fo_venda")
        self.website.company_id.sale_fiscal_operation_id = operation
        self.product.tax_icms_or_issqn = "issqn"
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
            self.start_tour(self.product.website_url, "l10n_br_website_sale_oca_tour")
        self.assertTrue(cep.called)
        self.assertEqual(cep.call_args.args[0], "12246250")
        order = self._get_checkout_order("checkout-br@example.com")
        self.assertEqual(order.order_line.fiscal_operation_id, operation)
        self.assertEqual(
            order.order_line.fiscal_operation_line_id,
            self.env.ref("l10n_br_fiscal.fo_venda_servico"),
        )
        partner = order.partner_invoice_id
        self.assertEqual(order.partner_id, partner)
        self.assertEqual(partner.state_id, self.city.state_id)
        self.assertEqual(partner.city_id, self.city)
        self.assertEqual(partner.street_name, "Rua do Aruana")
        self.assertEqual(partner.street_number, "200")
        self.assertEqual(partner.district, "Parque Residencial Aquarius")
        self.assertEqual(partner.zip, "12246-250")
        self.assertEqual(partner.vat, "89604455095")
        self.assertEqual(partner.l10n_br_ie_code, "110042490114")

    def test_foreign_checkout(self):
        country = self.env.ref("base.fr")
        self.start_tour(
            self.product.website_url,
            "l10n_br_website_sale_oca_foreign_tour",
        )
        partner = self._get_checkout_order("checkout-fr@example.com").partner_invoice_id
        self.assertEqual(partner.country_id, country)
        self.assertEqual(partner.city, "Paris")
        self.assertEqual(partner.street, "1 rue de la Paix")
        self.assertFalse(partner.vat)
