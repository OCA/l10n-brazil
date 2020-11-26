# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_invoice_create(self):
        picking_ids = self.picking_ids.filtered(
            lambda p: p.invoice_state == '2binvoiced' and p.state == 'done')
        invoices = self.env['account.invoice']
        if picking_ids:
            wizard = self.env['stock.invoice.onshipping'].with_context(
                active_model='stock.picking',
                active_ids=picking_ids.ids).create({})
            wizard.write(wizard.default_get(wizard.fields_get().keys()))
            invoices = wizard._action_generate_invoices()
            wizard._update_picking_invoice_status(
                invoices.mapped("picking_ids"))
        result = super().action_invoice_create()
        return result + invoices.ids
