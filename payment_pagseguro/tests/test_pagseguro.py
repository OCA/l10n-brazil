# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time

import odoo
from odoo.exceptions import ValidationError


@odoo.tests.tagged("post_install", "-at_install")
class PagseguroTest(odoo.tests.HttpCase):
    def setUp(self):
        super(PagseguroTest, self).setUp()

        self.eur_currency = self.env["res.currency"].search([("name", "=", "EUR")])
        self.brl_currency = self.env["res.currency"].search([("name", "=", "BRL")])

    def test_buy_pagseguro(self):
        self.browser_js(
            "/shop",
            "odoo.__DEBUG__.services['web_tour.tour'].run('shop_buy_pagseguro')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.shop_buy_pagseguro.ready",
            login="admin",
            timeout=20000,
        )

        tx = self.env["payment.transaction"].search([], limit=1, order="id desc")
        self.set_transaction_currency(tx, self.eur_currency)

        with self.assertRaises(ValidationError):
            tx.pagseguro_s2s_capture_transaction()

        self.set_transaction_currency(tx, self.brl_currency)

        tx.pagseguro_s2s_capture_transaction()
        self.assertEqual(tx.state, "done", "transaction state should be authorized")

        time.sleep(3)
        tx.pagseguro_s2s_void_transaction()
        self.assertEqual(tx.state, "done", "transaction state should be done")

    @staticmethod
    def set_transaction_currency(transaction, currency):
        for order in transaction.sale_order_ids:
            order.currency_id = currency.id
