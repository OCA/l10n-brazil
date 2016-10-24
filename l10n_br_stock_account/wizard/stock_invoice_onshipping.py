# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import ast

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class StockInvoiceOnShipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    journal_id = fields.Many2one(
        'account.journal', 'Destination Journal',
        domain="[('type', '=', journal_type)]")
    fiscal_category_journal = fields.Boolean(
        u'Diário da Categoria Fiscal', default=True)

    @api.multi
    def open_invoice(self):
        context = dict(self.env.context)
        for wizard in self:
            fiscal_document_code = (wizard.journal_id.company_id.
                                    product_invoice_id.code)
            context.update(
                {'fiscal_document_code': fiscal_document_code})
        result = super(StockInvoiceOnShipping,
                       self.with_context(context)).open_invoice()
        if result.get('context'):
            super_context = ast.literal_eval(result.get('context'))
            super_context.update(context)
            result['context'] = str(super_context)
        return result

    @api.multi
    def create_invoice(self):
        context = dict(self.env.context)
        active_ids = context.get('active_ids', [])
        for picking in self.env['stock.picking'].browse(active_ids):
            journal_id = picking.fiscal_category_id.property_journal
            fiscal_document_code = picking.company_id.product_invoice_id.code
            context.update(
                {'fiscal_document_code': fiscal_document_code})
            if not journal_id:
                raise UserError(
                    _('Invalid Journal!'),
                    _('There is not journal defined for this company: %s in '
                      'fiscal operation: %s !') %
                    (picking.company_id.name,
                     picking.fiscal_category_id.name))
            self.write({'journal_id': journal_id.id})
        result = super(StockInvoiceOnShipping,
                       self.with_context(context)).create_invoice()
        return result
