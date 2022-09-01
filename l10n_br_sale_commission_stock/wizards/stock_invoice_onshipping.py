# Copyright (C) 2022  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        """
        Copies sale commission agents data in sale order line to invoice line
        :param moves: stock.move
        :param invoice_values: new invoice line values dict
        :param invoice: account.invoice
        :return: dict
        """

        values = super()._get_invoice_line_values(moves, invoice_values, invoice)

        if len(moves) == 1:
            if moves.sale_line_id:
                values["agents"] = [
                    (0, 0, {"agent": x.agent.id, "commission": x.commission.id})
                    for x in moves.sale_line_id.agents
                ]

        return values
