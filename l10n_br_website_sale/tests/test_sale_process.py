import odoo.tests


@odoo.tests.tagged('post_install', '-at_install')
class TestUi(odoo.tests.HttpCase):
    def test_01_l10n_br_website_sale_tour(self):
        tour = (
            "odoo.__DEBUG__.services['web_tour.tour']",
            "l10n_br_website_sale_tour",
        )
        self.phantom_js(
            url_path="/shop",
            code="%s.run('%s')" % tour,
            ready="%s.tours.%s.ready" % tour,
            login="admin",
            timeout=5000
            )
        # check result
        record = self.env.ref('base.partner_admin')
        self.assertEqual(record.state_id.code, 'SP')
        self.assertEqual(record.city_id.ibge_code, '3549904')
