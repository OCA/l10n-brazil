from odoo.tests.common import HttpCase


class TestUi(HttpCase):
    def test_01_l10n_br_website_sale_tour(self):
        tour = (
            "odoo.__DEBUG__.services['web_tour.tour']",
            "l10n_br_website_sale_tour",
            )
        self.browser_js(
            url_path="/shop",
            code="%s.run('%s')" % tour,
            ready="%s.tours.%s.ready" % tour,
            login="admin",
            timeout=20000
            )
        # check result
        record = self.env.ref('base.partner_admin')
        record = self.env['sale.order'].search(
            [('partner_id', '=', record.id)], limit=1).partner_shipping_id
        self.assertEqual(record.state_id.code, 'SP')
        self.assertEqual(record.city_id.ibge_code, '49904')
