# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from unittest import mock

from odoo.tests import HttpCase, tagged

_module_ns = "odoo.addons.l10n_br_zip"
_provider_class = _module_ns + ".models.l10n_br_zip" + ".L10nBrZip"


@tagged("post_install", "-at_install")
class TestUi(HttpCase):
    def test_01_l10n_br_portal_load_tour(self):
        mocked_response = {
            "zip_code": "37500015",
            "street_name": " Rua Coronel Renno",
            "district": "Centro",
            "city_id": self.env.ref("l10n_br_base.city_3132404").id,
            "state_id": self.env.ref("base.state_br_mg").id,
            "country_id": self.env.ref("base.br").id,
        }
        with mock.patch(
            _provider_class + "._consultar_cep",
            return_value=mocked_response,
        ):
            self.start_tour("/my/account", "l10n_br_portal_tour", login="admin")
        # check result
        record = self.env.ref("base.partner_admin")
        self.assertEqual(record.country_id.code, "BR")
        self.assertEqual(record.state_id.code, "MG")
        self.assertEqual(record.city_id.ibge_code, "3132404")

        record.create_company()
        partner = self.env["res.partner"].search(
            [
                ("name", "=", "Empresa X"),
            ],
            limit=1,
        )
        self.assertEqual(partner.l10n_br_ie_code, record.l10n_br_ie_code)
        self.assertEqual(partner.l10n_br_im_code, record.l10n_br_im_code)
