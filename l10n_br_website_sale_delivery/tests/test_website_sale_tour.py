import odoo.tests


@odoo.tests.tagged('post_install', '-at_install')
class TestUi(odoo.tests.HttpCase):
    def test_01_l10n_br_website_sale_delivery_tour(self):
        self.env.ref("delivery.free_delivery_carrier").sudo().write({
            'fixed_price': 7,
            'free_over': True,
            'amount': 10000,
            })
        tour = (
            "odoo.__DEBUG__.services['web_tour.tour']",
            "l10n_br_website_sale_delivery_tour",
            )
        self.phantom_js(
            url_path="/shop",
            code="%s.run('%s')" % tour,
            ready="%s.tours.%s.ready" % tour,
            login="admin",
            timeout=5000
            )
        # check result
        record = self.env['sale.order'].search(
            [], limit=1)
        self.assertEqual(record.amount_freight, 7.0)
