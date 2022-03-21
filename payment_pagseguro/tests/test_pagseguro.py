# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

import odoo
from odoo.exceptions import ValidationError


@odoo.tests.tagged("post_install", "-at_install")
class PagseguroTest(odoo.tests.HttpCase):
    def test_buy_pagseguro(self):
        self.browser_js(
            "/shop",
            "odoo.__DEBUG__.services['web_tour.tour'].run('shop_buy_pagseguro')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.shop_buy_pagseguro.ready",
            login="admin",
            timeout=20000,
        )

        tx = self.env["payment.transaction"].search([], limit=1, order="id desc")
        with self.assertRaises(ValidationError):
            tx.pagseguro_s2s_capture_transaction()

        brl_currency = self.env["res.currency"].search([("name", "=", "BRL")])
        for order in tx.sale_order_ids:
            order.currency_id = brl_currency.id

        tx.pagseguro_s2s_capture_transaction()
        self.assertEqual(tx.state, "done", "transaction state should be authorized")

        time.sleep(3)
        tx.pagseguro_s2s_void_transaction()
        self.assertEqual(tx.state, "done", "transaction state should be done")
