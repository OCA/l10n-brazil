# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

import odoo.tests


@odoo.tests.tagged('post_install', '-at_install')
class TestUi(odoo.tests.HttpCase):
    def test_01_l10n_br_portal_load_tour(self):
        self.phantom_js(
            "/",
            "odoo.__DEBUG__.services['web_tour.tour'].run('l10n_br_portal_tour')",  # noqa: E501
            "odoo.__DEBUG__.services['web_tour.tour'].tours.l10n_br_portal_tour.ready",  # noqa: E501
            login="portal"
        )
        # check result
        record = self.env.ref('base.partner_demo_portal')
        self.assertEqual(record.name, 'Joe Doe Inc')
        self.assertEqual(record.legal_name, 'JOE DOE LTDA')
        self.assertEqual(record.cnpj_cpf, '89604455095')
        self.assertEqual(record.country_id.code, 'BR')
        self.assertEqual(record.state_id.code, 'MG')
        self.assertEqual(record.city_id.ibge_code, '32404')
