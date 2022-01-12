# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo
from odoo.tests.common import HttpCase


@odoo.tests.tagged("post_install", "-at_install")
class PagseguroTest(HttpCase):
    def test_buy_pagseguro(self):
        self.browser_js(
            "/",
            "odoo.__DEBUG__.services['web_tour.tour'].run('shop_buy_pagseguro')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.shop_buy_pagseguro.ready",
            login="admin",
            timeout=40 * 60,
        )
