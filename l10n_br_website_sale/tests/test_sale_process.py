from odoo.tests.common import HttpCase


class TestUi(HttpCase):
    def test_01_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_02_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_03_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_04_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_05_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_06_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_07_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_08_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_09_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_010_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_011_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_012_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_013_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_014_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_015_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_016_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_017_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_018_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_019_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_020_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_021_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_022_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_023_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_024_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_025_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_026_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_027_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_028_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_029_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))

    def test_030_l10n_br_website_sale_tour(self):
        for i in range(1, 31):
            print("Running website_sale_tour test #" + str(i))
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
            self.assertEqual(record.zip, '12246250')
            self.assertEqual(record.state_id.code, 'SP')
            self.assertEqual(record.city_id.ibge_code, '49904')
            print("PASSED website_sale_tour test #" + str(i))
































