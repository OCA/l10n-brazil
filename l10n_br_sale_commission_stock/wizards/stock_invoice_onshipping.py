# Copyright (C) 2022  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"


    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        values = super()._get_invoice_line_values(moves, invoice_values, invoice)
        for move in moves:
            sale_line = move.sale_line_id
            if sale_line:
                agents_data = []
                for agent in sale_line.agent_ids:
                    agents_data.append((0, 0, {
                        "agent_id": agent.agent_id.id,
                        "commission_id": agent.commission_id.id
                    }))
                values["agent_ids"] = agents_data
        return values
