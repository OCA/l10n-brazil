# Copyright (C) 2019-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class StockRuleTest(TransactionCase):
    """Test Stock Rule"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a product route containing a stock rule that will
        # generate a move from Stock for every procurement created in Output
        cls.product_route = cls.env["stock.route"].create(
            {
                "name": "Stock -> output route",
                "product_selectable": True,
                "rule_ids": [
                    Command.create(
                        {
                            "name": "Stock -> output rule",
                            "action": "pull",
                            "picking_type_id": cls.env.ref(
                                "stock.picking_type_internal"
                            ).id,
                            "location_src_id": cls.env.ref(
                                "stock.stock_location_stock"
                            ).id,
                            "location_dest_id": cls.env.ref(
                                "stock.stock_location_output"
                            ).id,
                            "location_dest_from_rule": True,
                            "invoice_state": "2binvoiced",
                            "fiscal_operation_id": cls.env.ref(
                                "l10n_br_fiscal.fo_venda"
                            ).id,
                        },
                    )
                ],
            }
        )

        # Product and Partner created by the test, so the tests do not depend
        # on demo data
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product - Stock Rule",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test Partner - Stock Rule"}
        )

        # Set this route on the test product
        cls.product.write({"route_ids": [Command.link(cls.product_route.id)]})

    def test_01_procument_order(self):
        """Test Stock Rule create stock.move with Fiscal fields.

        No fim o Form do stock.rule também é exercitado: a Regra de
        recebimento é arquivada e uma Regra em "looping" (origem e destino
        iguais) é criada -- o `_get_custom_move_fields` do módulo não pode
        fazer o procurement entrar em loop com ela.
        """
        # Create Delivery Order of 10 units of the test product
        # from Output -> Customer
        product = self.product
        vals = {
            "name": "Delivery order for procurement",
            "partner_id": self.partner.id,
            "picking_type_id": self.ref("stock.picking_type_out"),
            "location_id": self.ref("stock.stock_location_output"),
            "location_dest_id": self.ref("stock.stock_location_customers"),
            "move_ids": [
                Command.create(
                    {
                        "name": "/",
                        "product_id": product.id,
                        "product_uom": product.uom_id.id,
                        "product_uom_qty": 10.00,
                        "procure_method": "make_to_order",
                        "location_id": self.ref("stock.stock_location_output"),
                        "location_dest_id": self.ref("stock.stock_location_customers"),
                    },
                )
            ],
        }
        pick_output = self.env["stock.picking"].create(vals)

        # Operação Fiscal no Move de ORIGEM (make_to_order): precisa chegar no
        # Move criado pela Regra (ver _prepare_procurement_values do stock.move)
        move_orig = pick_output.move_ids
        move_orig.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")

        # Nos `values` do procurement o `company_id` tem de ser um recordset: o
        # core usa `values['company_id'].ids` no stock.rule._get_rule_domain
        # (onde a record rule não filtra a Regra por empresa) e é o formato
        # usado por quem preenche os values no core
        # sale.order.line e stock.rule.run
        procurement_values = move_orig._prepare_procurement_values()
        self.assertIn("company_id", procurement_values)
        self.assertEqual(procurement_values["company_id"], move_orig.company_id)
        self.assertTrue(
            procurement_values["company_id"].ids,
            "`company_id` nos values do procurement deve ser recordset.",
        )

        # Confirm delivery order.
        pick_output.action_confirm()

        # I run the scheduler.
        # Note: If purchase if already installed, the method _run_buy
        # will be called due to the purchase demo data. As we update the
        # stock module to run this test, the method won't be an attribute
        # of stock.procurement at this moment. For that reason we mute the
        # logger when running the scheduler.
        with mute_logger("odoo.addons.stock.models.procurement"):
            self.env["procurement.group"].run_scheduler()

        # Check that a picking was created from stock to output.
        moves = self.env["stock.move"].search(
            [
                ("product_id", "=", self.product.id),
                ("location_id", "=", self.ref("stock.stock_location_stock")),
                ("location_dest_id", "=", self.ref("stock.stock_location_output")),
                ("move_dest_ids", "in", [pick_output.move_ids[0].id]),
            ]
        )
        self.assertEqual(
            len(moves.ids),
            1,
            "It should have created a picking from Stock to Output with the"
            " original picking as destination",
        )

        # Check if the fields included in l10n_br_stock_account was copied to move
        for move in moves:
            # A Operação Fiscal informada na Regra chegou no Move criado pelo
            # procurement (ver _get_stock_move_values do stock.rule) -- comparar
            # com o registro e não com o nome traduzido da Operação
            self.assertEqual(
                move.fiscal_operation_id,
                self.env.ref("l10n_br_fiscal.fo_venda"),
                "The stock.move created has not the Fiscal Operation of the rule.",
            )
            self.assertEqual(
                move.invoice_state,
                "2binvoiced",
                "The stock.move created has not invoice_state field 2binvoiced",
            )
            # Os campos do mixin de linha fiscal propagados (_get_custom_move_fields)
            # NÃO podem sobrescrever os campos do core com semântica diferente:
            # com `quantity` promovido o Move nasceria em "assigned" e o Picking
            # não seria criado (ver o comentário no override do stock.rule)
            self.assertEqual(
                move.product_uom_qty,
                10.0,
                "The quantity of the core Stock Move was changed.",
            )
            self.assertEqual(
                move.quantity,
                0.0,
                "The mixin quantity field must not be propagated to the Move.",
            )
            self.assertEqual(move.uom_id, self.product.uom_id)
            # O Move criado pela Regra herda os dados fiscais do Move de origem
            # (Operação Fiscal -> Linha da Operação Fiscal e Impostos), ver
            # _prepare_procurement_values do stock.move
            self.assertEqual(
                move.fiscal_operation_line_id,
                move_orig.fiscal_operation_line_id,
                "The stock.move created has not the Fiscal Operation Line"
                " of the origin Move.",
            )
            self.assertEqual(
                move.fiscal_tax_ids,
                move_orig.fiscal_tax_ids,
                "The stock.move created has not the Fiscal Taxes of the origin Move.",
            )
            # O Picking de Stock -> Output foi criado pela Regra
            self.assertTrue(
                move.picking_id,
                "It should have created a picking from Stock to Output.",
            )
            self.assertEqual(move.picking_id.picking_type_id.code, "internal")

        # Form do stock.rule: Regra em looping (origem e destino iguais)
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        reception_route = warehouse.reception_route_id
        reception_route.rule_ids.action_archive()
        stock_rule_form = Form(self.env["stock.rule"])
        stock_rule_form.name = "Looping Rule"
        stock_rule_form.route_id = reception_route
        stock_rule_form.location_dest_id = warehouse.lot_stock_id
        stock_rule_form.location_src_id = warehouse.lot_stock_id
        stock_rule_form.action = "pull_push"
        stock_rule_form.procure_method = "make_to_order"
        stock_rule_form.picking_type_id = warehouse.int_type_id
        stock_rule_form.save()
