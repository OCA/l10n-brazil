# @ 2020 KMEE - kmee.com.br
#   Diego Paradeda <diego.paradeda@kme.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from unittest import mock

from odoo.tests import HttpCase, tagged

_module_ns = "odoo.addons.l10n_br_zip"
_provider_class = _module_ns + ".models.l10n_br_zip" + ".L10nBrZip"


@tagged("post_install", "-at_install")
class TestUi(HttpCase):
    def test_01_l10n_br_website_sale_tour(self):
        provider = self.env.ref("payment.payment_provider_demo")
        provider.sudo().write(
            {
                "state": "test",
            }
        )
        tour = (
            "odoo.__DEBUG__.services['web_tour.tour']",
            "l10n_br_website_sale_tour",
        )
        mocked_response = {
            "zip_code": "12246250",
            "street_name": " Rua do Aruana",
            "district": "Parque Residencial Aquarius",
            "city_id": self.env.ref("l10n_br_base.city_3500105").id,
            "state_id": self.env.ref("base.state_br_sp").id,
            "country_id": self.env.ref("base.br").id,
        }
        with mock.patch(
            _provider_class + "._consultar_cep",
            return_value=mocked_response,
        ):
            self.browser_js(
                url_path="/shop",
                code=f"{tour[0]}.run('{tour[1]}')",
                ready=f"{tour[0]}.tours.{tour[1]}.ready",
                login="admin",
                timeout=20000,
            )
        # check result
        record = self.env.ref("base.partner_admin")
        record = (
            self.env["sale.order"]
            .search([("partner_id", "=", record.id)], limit=1)
            .partner_shipping_id
        )
        self.assertEqual(record.state_id.code, "SP")
        self.assertEqual(record.city_id.ibge_code, "3500105")
