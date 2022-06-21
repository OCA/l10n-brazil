# Copyright 2020, KMEE - kmee.com.br - Diego Paradeda <diego.paradeda@kmee.com.br>
# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests import HttpCase, tagged

_module_ns = "odoo.addons.l10n_br_zip"
_provider_class = _module_ns + ".models.l10n_br_zip" + ".L10nBrZip"


@tagged("post_install", "-at_install")
class TestUi(HttpCase):
    def test_01_l10n_br_website_sale_delivery_tour(self):
        self.product_delivery_poste = self.env["product.product"].create(
            {
                "name": "The Test Poste",
                "type": "service",
                "categ_id": self.env.ref("delivery.product_category_deliveries").id,
                "sale_ok": False,
                "purchase_ok": False,
                "list_price": 20.0,
            }
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "The Test Poste",
                "sequence": 9999,  # ensure last to load price async
                "fixed_price": 20.0,
                "delivery_type": "fixed",
                "product_id": self.product_delivery_poste.id,
                "website_published": True,
            }
        )

        mocked_response = {
            "zip_code": "12246250",
            "street_name": "Rua do Aruana",
            "district": "Parque Residencial Aquarius",
            "city_id": self.env.ref("l10n_br_base.city_3549904").id,
            "state_id": self.env.ref("base.state_br_sp").id,
            "country_id": self.env.ref("base.br").id,
        }
        with mock.patch(
            _provider_class + "._consultar_cep",
            return_value=mocked_response,
        ):
            self.start_tour(
                "/shop",
                "l10n_br_website_sale_delivery_tour",
                login="admin",
                timeout=5000,
            )
        # check result
        record = self.env["sale.order"].search([], limit=1)
        self.assertEqual(record.amount_freight_value, 20.0)
