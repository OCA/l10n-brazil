# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from unittest import mock

from odoo.tests import tagged
from odoo.tests import HttpCase

_module_ns = 'odoo.addons.l10n_br_zip'
_provider_class = (
    _module_ns
    + '.models.l10n_br_zip'
    + '.L10nBrZip'
)


@tagged('post_install', '-at_install')
class TestUi(HttpCase):

    def test_01_l10n_br_portal_load_tour(self):
        tour = (
            "odoo.__DEBUG__.services['web_tour.tour']",
            "l10n_br_portal_tour",
        )

        mocked_response = {
            "zip_code": '37500015',
            "street": " Rua Coronel Renno",
            "district": "Centro",
            "city_id": self.env.ref('l10n_br_base.city_3132404').id,
            "state_id": self.env.ref('base.state_br_mg').id,
            "country_id": self.env.ref('base.br').id,
        }
        with mock.patch(
                _provider_class + '._consultar_cep',
                return_value=mocked_response,
        ):
            self.phantom_js(
                url_path="/my/account",
                code="%s.run('%s')" % tour,
                ready="%s.tours['%s'].ready" % tour,
                login="admin",
                timeout=180
            )
        # check result
        record = self.env.ref('base.partner_admin')
        self.assertEqual(record.country_id.code, 'BR')
        self.assertEqual(record.state_id.code, 'MG')
        self.assertEqual(record.city_id.ibge_code, '32404')
