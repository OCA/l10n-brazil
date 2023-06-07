# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields
from odoo.tests.common import TransactionCase


class TestL10nBrPosNfcePosOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env.company = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        self.pos_config = self.env.ref("l10n_br_pos.pos_config_presumido")
        self.product_id = self.env.ref("point_of_sale.desk_organizer_product_template")

    def test_01_nfce_create_from_ui(self):
        self.pos_config.update_pos_fiscal_map()
        self.pos_config.open_session_cb(check_coa=False)
        current_session = self.pos_config.current_session_id
        num_starting_orders = len(current_session.order_ids)
        generic_order = {
            "data": {
                "amount_paid": self.product_id.list_price,
                "amount_return": 0,
                "amount_tax": self.product_id.list_price,
                "amount_total": self.product_id.list_price,
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
                            "product_id": self.env["product.product"]
                            .search([("product_tmpl_id", "=", self.product_id.id)])
                            .id,
                            "price_unit": self.product_id.list_price,
                            "price_subtotal": self.product_id.list_price,
                            "price_subtotal_incl": self.product_id.list_price,
                            "qty": 1,
                            "tax_ids": [(6, 0, self.product_id.taxes_id.ids)],
                            "full_product_name": self.product_id.name,
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
                            "amount": self.product_id.list_price,
                            "name": fields.Datetime.now(),
                            "payment_method_id": self.env.ref(
                                "l10n_br_pos.presumido_dinheiro"
                            ).id,
                        },
                    ]
                ],
                "uid": "00042-003-0014",
                "user_id": self.env.uid,
                "to_invoice": True,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_65").id,
            },
            "id": "00042-003-0014",
        }
        self.env["pos.order"].create_from_ui([generic_order])

        self.assertTrue(
            current_session.order_ids[0].account_move, "No account move created."
        )

        self.assertEqual(
            num_starting_orders + 1,
            len(current_session.order_ids),
            "Submitted order not encoded",
        )

    def test_02_nfce_payment_with_credit(self):
        self.pos_config.open_session_cb(check_coa=False)
        current_session = self.pos_config.current_session_id
        num_starting_orders = len(current_session.order_ids)
        generic_order = {
            "data": {
                "amount_paid": self.product_id.list_price,
                "amount_return": 0,
                "amount_tax": self.product_id.list_price,
                "amount_total": self.product_id.list_price,
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
                            "product_id": self.env["product.product"]
                            .search([("product_tmpl_id", "=", self.product_id.id)])
                            .id,
                            "price_unit": self.product_id.list_price,
                            "price_subtotal": self.product_id.list_price,
                            "price_subtotal_incl": self.product_id.list_price,
                            "qty": 1,
                            "tax_ids": [(6, 0, self.product_id.taxes_id.ids)],
                            "full_product_name": self.product_id.name,
                        },
                    ]
                ],
                "name": "Order 00042-003-0015",
                "partner_id": self.pos_config.partner_id.id,
                "pos_session_id": current_session.id,
                "sequence_number": 3,
                "statement_ids": [
                    [
                        0,
                        0,
                        {
                            "amount": self.product_id.list_price,
                            "name": fields.Datetime.now(),
                            "payment_method_id": self.env.ref(
                                "l10n_br_pos.presumido_credito_visa"
                            ).id,
                        },
                    ]
                ],
                "uid": "00042-003-0015",
                "user_id": self.env.uid,
                "to_invoice": True,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_65").id,
            },
            "id": "00042-003-0015",
        }
        self.env["pos.order"].create_from_ui([generic_order])

        self.assertTrue(
            current_session.order_ids[0].account_move, "No account move created."
        )
        self.assertEqual(
            num_starting_orders + 1,
            len(current_session.order_ids),
            "Submitted order not encoded",
        )

    def test_03_nfce_payment_with_pix(self):
        self.pos_config.open_session_cb(check_coa=False)
        current_session = self.pos_config.current_session_id
        num_starting_orders = len(current_session.order_ids)
        generic_order = {
            "data": {
                "amount_paid": self.product_id.list_price,
                "amount_return": 0,
                "amount_tax": self.product_id.list_price,
                "amount_total": self.product_id.list_price,
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
                            "product_id": self.env["product.product"]
                            .search([("product_tmpl_id", "=", self.product_id.id)])
                            .id,
                            "price_unit": self.product_id.list_price,
                            "price_subtotal": self.product_id.list_price,
                            "price_subtotal_incl": self.product_id.list_price,
                            "qty": 1,
                            "tax_ids": [(6, 0, self.product_id.taxes_id.ids)],
                            "full_product_name": self.product_id.name,
                        },
                    ]
                ],
                "name": "Order 00042-003-0016",
                "partner_id": self.pos_config.partner_id.id,
                "pos_session_id": current_session.id,
                "sequence_number": 4,
                "statement_ids": [
                    [
                        0,
                        0,
                        {
                            "amount": self.product_id.list_price,
                            "name": fields.Datetime.now(),
                            "payment_method_id": self.env.ref(
                                "l10n_br_pos.presumido_pix"
                            ).id,
                        },
                    ]
                ],
                "uid": "00042-003-0016",
                "user_id": self.env.uid,
                "to_invoice": True,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_65").id,
            },
            "id": "00042-003-0016",
        }
        self.env["pos.order"].create_from_ui([generic_order])

        self.assertTrue(
            current_session.order_ids[0].account_move, "No account move created."
        )
        self.assertEqual(
            num_starting_orders + 1,
            len(current_session.order_ids),
            "Submitted order not encoded",
        )

    def test_04_nfce_cancel_from_ui(self):
        self.pos_config.open_session_cb(check_coa=False)
        current_session = self.pos_config.current_session_id
        order = current_session.order_ids[0]
        order.account_move.fiscal_document_id.write(
            {"authorization_protocol": fields.Datetime.now()}
        )
        self.env["pos.order"].cancel_nfce_from_ui(order["pos_reference"], "Teste")

        self.assertEqual(order.state, "cancel", "Order not cancelled")
        current_session.action_pos_session_closing_control()
