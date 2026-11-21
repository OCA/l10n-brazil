# Copyright 2022 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase


class TestL10nBrPosOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.pos_config = cls.env.ref("l10n_br_pos.pos_config_presumido")
        cls.cash_payment_method = cls.env.ref("l10n_br_pos.presumido_dinheiro")
        cls.led_lamp = cls.env["product.product"].create(
            {
                "name": "LED Lamp",
                "available_in_pos": True,
                "list_price": 0.90,
            }
        )

    def compute_tax(self, product, price, qty=1, taxes=None):
        if not taxes:
            taxes = product.taxes_id.filtered(
                lambda t: t.company_id.id == self.env.company.id
            )
        currency = self.pos_config.pricelist_id.currency_id
        res = taxes.compute_all(price, currency, qty, product=product)
        untax = res["total_excluded"]
        return untax, sum(tax.get("amount", 0.0) for tax in res["taxes"])

    def _generate_order(self):
        current_session = self.pos_config.current_session_id
        untax, atax = self.compute_tax(self.led_lamp, 0.9)
        generic_order = {
            "amount_paid": untax + atax,
            "amount_return": 0,
            "amount_tax": atax,
            "amount_total": untax + atax,
            "date_order": fields.Datetime.to_string(fields.Datetime.now()),
            "fiscal_position_id": False,
            "pricelist_id": self.pos_config.pricelist_id.id,
            "last_order_preparation_change": "{}",
            "lines": [
                [
                    0,
                    0,
                    {
                        "discount": 0,
                        "pack_lot_ids": [],
                        "price_unit": 0.9,
                        "product_id": self.led_lamp.id,
                        "price_subtotal": 0.9,
                        "price_subtotal_incl": 1.04,
                        "qty": 1,
                        "tax_ids": [(6, 0, self.led_lamp.taxes_id.ids)],
                    },
                ]
            ],
            "name": "Order 00042-003-0014",
            "partner_id": False,
            "session_id": current_session.id,
            "sequence_number": 2,
            "payment_ids": [
                [
                    0,
                    0,
                    {
                        "amount": untax + atax,
                        "name": fields.Datetime.now(),
                        "payment_method_id": self.cash_payment_method.id,
                    },
                ]
            ],
            "uuid": "00042-003-0014",
            "user_id": self.env.uid,
            "to_invoice": False,
            "authorization_date": "2022-01-01 12:00:00",
            "document_number": "123456",
            "document_key": "35181104113837000100650010000000011234567890",
            "document_type_id": self.env.ref("l10n_br_fiscal.document_65").id,
            "document_serie": "123456789",
            "fiscal_operation_id": self.pos_config.out_pos_fiscal_operation_id.id,
            "status_code": "06000",
            "status_name": "Autorizado o uso da NFC-e",
            "state_edoc": "autorizada",
        }
        self.env["pos.order"].sync_from_ui([generic_order])

    def test_sync_from_ui_l10n_brazil(self):
        session = self.env["pos.session"].create(
            {"config_id": self.pos_config.id, "user_id": self.env.uid}
        )
        session.action_pos_session_open()

        current_session = self.pos_config.current_session_id
        num_starting_orders = len(current_session.order_ids)

        self._generate_order()

        orders_exported_to_ui = current_session.order_ids.read_pos_data(
            [], self.pos_config.id
        )["pos.order"]

        self.assertEqual(
            num_starting_orders + 1,
            len(current_session.order_ids),
            "Submitted order not encoded",
        )

        self.assertEqual(
            1,
            len(orders_exported_to_ui),
            "Orders not exported to UI.",
        )
