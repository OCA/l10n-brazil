# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, models
from odoo.exceptions import UserError


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _create_returns(self):
        """
        Creates return picking.
        @param self: The object pointer.
        @return: A dictionary which of fields with values.
        """
        new_picking_id, pick_type_id = super()._create_returns()

        picking_obj = self.env["stock.picking"]
        picking = picking_obj.browse(new_picking_id)

        origin_picking = self.env["stock.picking"].browse(self.env.context["active_id"])

        if origin_picking.fiscal_operation_id:

            refund_fiscal_operation = (
                origin_picking.fiscal_operation_id.return_fiscal_operation_id
            )

            if not refund_fiscal_operation:
                if self.invoice_state == "2binvoiced":
                    raise UserError(
                        _(
                            "This Fiscal Operation has no Fiscal Operation"
                            " for Returns defined!"
                        )
                    )
            else:
                picking.fiscal_operation_id = refund_fiscal_operation.id
                move_obj = self.env["stock.move"]
                for move in picking.move_lines:
                    ret_move = move.origin_returned_move_id
                    fiscal_op = ret_move.fiscal_operation_id.return_fiscal_operation_id
                    fiscal_op_line = ret_move.fiscal_operation_line_id.line_refund_id

                    line_values = {
                        "fiscal_operation_id": fiscal_op.id,
                        "fiscal_operation_line_id": fiscal_op_line.id,
                    }
                    write_move = move_obj.browse(move.id)
                    write_move.write(line_values)
                    write_move._onchange_product_id_fiscal()
                    write_move._onchange_fiscal_operation_id()
                    write_move._onchange_fiscal_operation_line_id()

        return new_picking_id, pick_type_id
