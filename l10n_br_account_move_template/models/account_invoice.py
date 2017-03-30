# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def invoice_line_move_line_get(self):
        result = []
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        if self.company_id.use_moves_line_templates:
            mlt_obj = self.env['account.move.template']
            for move_line in res:
                result.append(mlt_obj.map_account(move_line))
        return result

    @api.model
    def tax_line_move_line_get(self):
        result = []
        res = super(AccountInvoice, self).tax_line_move_line_get()
        if self.company_id.use_moves_line_templates:
            mlt_obj = self.env['account.move.template']
            for move_line in res:
                result.append(mlt_obj.map_account(move_line))
        return result
