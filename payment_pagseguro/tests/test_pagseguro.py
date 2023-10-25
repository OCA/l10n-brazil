# # Copyright 2020 KMEE INFORMATICA LTDA
# # License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import time

import vcr

import odoo
from odoo.exceptions import ValidationError


@odoo.tests.tagged("post_install", "-at_install")
class PagseguroTest(odoo.tests.HttpCase):
    def setUp(self):
        super().setUp()

        self.eur_currency = self.env["res.currency"].search([("name", "=", "EUR")])
        self.brl_currency = self.env["res.currency"].search([("name", "=", "BRL")])

    @vcr.use_cassette(
        os.path.dirname(__file__) + "/fixtures/test_buy_pagseguro.yaml",
        match_on=["method", "scheme", "host", "port", "path", "query", "body"],
        filter_post_data_parameters=[
            "description",
            "reference_id",
            "payment_method",
            "charge_id",
            "amount",
        ],
        ignore_localhost=True,
    )
    def test_buy_pagseguro(self):
        self.start_tour(
            "/shop",
            "shop_buy_pagseguro",
            login="admin",
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

    @vcr.use_cassette(
        os.path.dirname(__file__) + "/fixtures/test_buy_pagseguro_fail.yaml"
    )
    def test_buy_pagseguro_fail(self):
        pagseguro_acquirer = self.env.ref(
            "payment_pagseguro.payment_acquirer_pagseguro"
        )
        pagseguro_acquirer.write(
            {
                "pagseguro_token": "70490B37BABA1C2EE4F4FFB244ED8425",
                "journal_id": 1,
                "payment_flow": "s2s",
            }
        )

        buyer = self.env["res.partner"].create({"name": "Buyer"})

        payment_token = self.env["payment.token"].create(
            {
                "acquirer_ref": buyer.id,
                "acquirer_id": pagseguro_acquirer.id,
                "partner_id": buyer.id,
                "cc_holder_name": buyer.name,
                "pagseguro_card_token": "wrongcardtoken",
                "pagseguro_payment_method": "CREDIT_CARD",
                "pagseguro_installments": 1,
            }
        )

        transaction = self.env["payment.transaction"].create(
            {
                "reference": "test_ref_10001",
                "currency_id": self.brl_currency.id,
                "acquirer_id": pagseguro_acquirer.id,
                "partner_id": buyer.id,
                "payment_token_id": payment_token.id,
                "type": "server2server",
                "amount": 100.0,
            }
        )

        self.assertFalse(transaction.pagseguro_s2s_do_transaction())
