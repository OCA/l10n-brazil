# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api

FISCAL_DOC_REF = [
    ('pos.order', u'Pedido do PDV')
]



class StockInvoiceOnShipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def _fiscal_doc_ref_selection(self):
        prev = super(StockInvoiceOnShipping, self)._fiscal_doc_ref_selection()
        return prev + FISCAL_DOC_REF

    @api.multi
    def _fiscal_doc_ref_default(self):
        result = super(StockInvoiceOnShipping, self)._fiscal_doc_ref_default()
        id_in_model = result.split(',')[1]
        if id_in_model != '0':
            return result
        else:
            picking_obj = self.env['stock.picking']
            for record in picking_obj.browse(
                    self._context.get('active_ids', False)):
                move = record.move_lines[0]
                if move.origin_returned_move_id:
                    ref_id = self.env['pos.order'].search([
                        ('chave_cfe', '=',
                         move.origin_returned_move_id.
                         picking_id.fiscal_document_access_key)
                    ], limit=1).id
                    result = 'pos.order,%d' % ref_id
            return result
