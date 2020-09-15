# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

import odoo.tests


@odoo.tests.tagged('post_install', '-at_install')
class TestUi(odoo.tests.HttpCase):
    def test_01_l10n_br_portal_load_tour(self):
        tour = (
            "odoo.__DEBUG__.services['web_tour.tour']",
            "l10n_br_portal_tour",
        )
        self.phantom_js(
            url_path="/my/account",
            code="%s.run('%s')" % tour,
            ready="%s.tours['%s'].ready" % tour,
            login="portal",
            timeout=60
        )
        # check result
        record = self.env.ref('base.partner_demo_portal')
        self.assertEqual(record.country_id.code, 'BR')
        self.assertEqual(record.state_id.code, 'MG')
        self.assertEqual(record.city_id.ibge_code, '32404')
