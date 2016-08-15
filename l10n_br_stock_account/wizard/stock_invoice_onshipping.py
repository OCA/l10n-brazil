# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

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
    def create_invoice(self):
        context = self.env.context
        active_ids = context.get('active_ids', [])
        for picking in self.env['stock.picking'].browse(active_ids):
            journal_id = picking.fiscal_category_id.property_journal
            if not journal_id:
                raise UserError(
                    _('Invalid Journal!'),
                    _('There is not journal defined for this company: %s in '
                      'fiscal operation: %s !') %
                    (picking.company_id.name,
                     picking.fiscal_category_id.name))
            self.write({'journal_id': journal_id.id})
        result = super(StockInvoiceOnShipping, self).create_invoice()
        return result
