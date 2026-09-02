# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, models
from odoo.exceptions import UserError


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _prepare_picking_default_values(self):
        """
        Inform the return Fiscal Operation on the new return picking.
        """
        vals = super()._prepare_picking_default_values()
        if self.picking_id.fiscal_operation_id:
            refund_fiscal_operation = (
                self.picking_id.fiscal_operation_id.return_fiscal_operation_id
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
                vals["fiscal_operation_id"] = refund_fiscal_operation.id
        return vals


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    def _prepare_move_default_values(self, new_picking):
        """
        Inform the return Fiscal Operation (and its line) on the return moves.
        """
        vals = super()._prepare_move_default_values(new_picking)
        if self.move_id.fiscal_operation_id:
            fiscal_op = self.move_id.fiscal_operation_id.return_fiscal_operation_id
            if fiscal_op:
                vals["fiscal_operation_id"] = fiscal_op.id
                refund_line = fiscal_op.line_definition(
                    self.move_id.company_id, self.move_id.partner_id, self.product_id
                )
                if refund_line:
                    vals["fiscal_operation_line_id"] = refund_line.id
        return vals
