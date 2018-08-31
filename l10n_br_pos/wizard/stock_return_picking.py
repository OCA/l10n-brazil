# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api
from odoo.tools.safe_eval import safe_eval


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def create_returns(self):
        result = super(StockReturnPicking, self).create_returns()
        if self.mapped('product_return_moves.move_id.picking_id.pos_order_ids'):
            # Create the return process if the product came from
            # a pos.order.

            picking_devolucao = self.assign_returning_picking(
                result)

            if picking_devolucao.state != u'confirmed':
                self.transfer_returning_picking(picking_devolucao)

            # Create the wizard that relate the source fiscal documents with
            # the generated picking
            wizard_invoice = self.env['stock.invoice.onshipping'].with_context(
                active_ids=picking_devolucao.ids,
                active_model='stock.picking',
                company_id=picking_devolucao.company_id.id
            ).create({})

            # Generate the returning invoice
            res_domain_invoice = wizard_invoice.open_invoice()

            # Confirm and send to SEFAZ the created returning invoice
            picking_devolucao.invoice_id.signal_workflow('invoice_validate')

            return res_domain_invoice
        else:
            return result

    def transfer_returning_picking(self, picking_devolucao):
        # Create and do the transfer in the return wizard
        wizard_transfer = picking_devolucao.do_enter_transfer_details()
        stock_transfer_details_obj = self.env['stock.transfer_details']
        wizard_transfer_id = stock_transfer_details_obj.with_context(
            active_ids=wizard_transfer['context']['active_ids'],
            active_model=wizard_transfer['context']['active_model']
        ).create({'picking_id': picking_devolucao.id})
        wizard_transfer_id.do_detailed_transfer()

    def assign_returning_picking(self, result):
        # Search and assign the returning picking
        result_domain = safe_eval(result['domain'])
        picking_ids = result_domain and result_domain[0] and \
            result_domain[0][2]
        picking_devolucao = self.env['stock.picking'].browse(picking_ids)
        picking_devolucao.action_assign()
        return picking_devolucao
