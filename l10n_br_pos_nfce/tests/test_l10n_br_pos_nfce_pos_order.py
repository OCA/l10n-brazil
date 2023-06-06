# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields
from odoo.tests.common import TransactionCase


class TestL10nBrPosNfcePosOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env.company = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        self.pos_config = self.env.ref("l10n_br_pos.pos_config_presumido")
        self.pos_config.simplified_document_type_id = self.env.ref(
            "l10n_br_fiscal.document_65"
        ).id
        self.payment_method_id = self.env["account.payment.method"].create(
            {
                "name": "Manual Test NFCe",
                "code": "nfce",
                "payment_type": "inbound",
            }
        )
        vals = {
            "name": "Dinheiro",
            "payment_method_id": self.payment_method_id.id,
            "payment_type": "inbound",
            "fiscal_payment_mode": "01",
            "bank_account_link": "variable",
            "variable_journal_ids": [
                self.env.ref("l10n_br_pos.pos_sale_journal_presumido").id
            ],
        }
        self.account_payment_mode = self.env["account.payment.mode"].create(vals)
        self.cash_payment_method = self.env.ref("l10n_br_pos.presumido_dinheiro")
        self.cash_payment_method.write(
            {"payment_mode_id": [(1, 0, self.account_payment_mode.id)]}
        )
        self.led_lamp = self.env["product.product"].create(
            {
                "name": "LED Lamp",
                "available_in_pos": True,
                "list_price": 0.90,
            }
        )
        self.pos_config.partner_id = self.env.ref(
            "l10n_br_fiscal.res_partner_anonimo"
        ).id

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
            "data": {
                "amount_paid": untax + atax,
                "amount_return": 0,
                "amount_tax": atax,
                "amount_total": untax + atax,
                "creation_date": fields.Datetime.to_string(fields.Datetime.now()),
                "fiscal_position_id": False,
                "pricelist_id": self.pos_config.available_pricelist_ids[0].id,
                "lines": [
                    [
                        0,
                        0,
                        {
                            "discount": 0,
                            "id": 42,
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
                "partner_id": self.pos_config.partner_id.id,
                "pos_session_id": current_session.id,
                "sequence_number": 2,
                "statement_ids": [
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
                "uid": "00042-003-0014",
                "user_id": self.env.uid,
                "to_invoice": True,
            },
            "id": "00042-003-0014",
            "document_type_id": 33,
            "fiscal_operation_id": 1,
        }
        self.env["pos.order"].create_from_ui([generic_order])

    def test_nfce_create_from_ui(self):
        self.pos_config.update_pos_fiscal_map()
        self.pos_config.open_session_cb(check_coa=False)
        current_session = self.pos_config.current_session_id
        num_starting_orders = len(current_session.order_ids)
        self._generate_order()

        self.assertTrue(
            current_session.order_ids[0].account_move, "No account move created."
        )

        self.assertEqual(
            num_starting_orders + 1,
            len(current_session.order_ids),
            "Submitted order not encoded",
        )

    def test_l10n_br_pos_nfce_cancel_from_ui(self):
        self.pos_config.update_pos_fiscal_map()
        self.pos_config.open_session_cb(check_coa=False)
        current_session = self.pos_config.current_session_id
        num_starting_orders = len(current_session.order_ids)
        self._generate_order()
        order = current_session.order_ids[0]
        self.env["pos.order"].cancel_nfce_from_ui(order["pos_reference"], "Teste")
        self.assertEqual(
            num_starting_orders + 2,
            len(current_session.order_ids),
            "Cancelled order not encoded",
        )
