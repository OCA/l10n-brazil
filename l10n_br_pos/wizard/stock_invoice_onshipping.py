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
        if id_in_model == '0':
            return_picking_ids = self.get_returned_picking_ids()
            ref_id = return_picking_ids.mapped('pos_order_ids')[:1].id
            result = 'pos.order,%d' % ref_id
        return result
