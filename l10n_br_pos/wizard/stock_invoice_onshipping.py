# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class StockInvoiceOnShippingRelatedDocument(models.TransientModel):
    _inherit = 'stock.invoice.onshipping.related.document'

    @api.model
    def get_picking_document_relationships(self):
        return super(
            StockInvoiceOnShippingRelatedDocument, self
        ).get_picking_document_relationships() + [
            'move_lines.origin_returned_move_id.picking_id.pos_order_ids',
        ]

    @api.multi
    def compute_all_for_pos_order(self):
        self.document_type = "sat"
        document = self.fiscal_doc_ref
        self.document_date = document.date_order
        self.document_partner_id = document.partner_id
        self.document_amount = document.amount_total
        self.access_key = document.chave_cfe[3:]


class StockInvoiceOnShipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    @api.multi
    def create_invoice(self):
        result = super(StockInvoiceOnShipping, self).create_invoice()
        for document in self.related_document_ids:
            vals = {
                'invoice_id': result[0],
                'access_key': document.access_key,
                'document_type': document.document_type,
            }
            self.env['l10n_br_account_product.document.related'].create(vals)

        return result
