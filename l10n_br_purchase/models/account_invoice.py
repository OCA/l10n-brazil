# Copyright (C) 2020  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(
            AccountInvoice, self
        )._prepare_invoice_line_from_po_line(line)

        data['operation_id'] = line.operation_id.id
        data['operation_line_id'] = line.operation_line_id.id

        return data

    @api.model
    def create(self, values):

        values['purchase_id'] = values[
            'invoice_line_ids'][0][2].get('purchase_id')

        # TODO - Are we need to identify when should create fiscal document ?
        values['fiscal_document_id'] = False

        # TODO - Is there a better way to make it ? Should exist
        if values['invoice_line_ids'][0][2].get('purchase_id'):
            purchase = self.env['purchase.order'].browse(
                values['invoice_line_ids'][0][2].get('purchase_id'))

            values['operation_id'] = purchase.operation_id.id
            values['operation_type'] = purchase.operation_type

            for line in values['invoice_line_ids']:
                if line[2]['purchase_line_id']:
                    purchase_line = self.env[
                        'purchase.order.line'].browse(
                        line[2]['purchase_line_id'])
                    document_type_id = \
                        purchase_line.operation_line_id.get_document_type(
                            purchase_line.order_id.company_id).id
                    # TODO - Fields below should be filled by method
                    #  _prepare_invoice_line_from_po_line() above, but
                    #  the dict line[2] don't bring the fields, it's seems
                    #  there is another method removing the fields
                    line[2]['operation_id'] = purchase_line.operation_id.id
                    line[2]['operation_line_id'] = purchase_line.operation_line_id.id

            values['document_type_id'] = document_type_id

        invoice = super(AccountInvoice, self).create(values)

        return invoice
