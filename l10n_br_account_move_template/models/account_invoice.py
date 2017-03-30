# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def move_line_get(self, invoice_id):
        result = []
        res = super(AccountInvoiceLine, self).move_line_get(invoice_id)
        invoice = self.env['account.invoice'].browse(invoice_id)
        if invoice.company_id.use_move_line_templates:
            mlt_obj = self.env['account.move.template']
            for move_line in res:
                result.append(mlt_obj.map_account(move_line))
        return result


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    @api.model
    def move_line_get(self, invoice_id):
        result = []
        res = super(AccountInvoiceTax, self).move_line_get(invoice_id)
        invoice = self.env['account.invoice'].browse(invoice_id)
        if invoice.company_id.use_move_line_templates:
            mlt_obj = self.env['account.move.template']
            for move_line in res:
                result.append(mlt_obj.map_account(move_line))
        return result
