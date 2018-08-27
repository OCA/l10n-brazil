# -*- coding: utf-8 -*-
#    Copyright (C) 2012-TODAY KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo (mileo@kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp import models, api

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        value = super(AccountInvoice, self).action_move_create()

        for invoice in self:
            sequence = self.env['ir.sequence'].next_by_id(
                self.company_id.transaction_id_sequence.id)
            invoice.transaction_id = sequence

        return value

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ Propagate the transaction_id from the invoice to the move lines.

        The transaction id is written on the move lines only if the account is
        the same than the invoice's one.
        """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)
        for invoice in self:
            if invoice.transaction_id:
                invoice_account_id = invoice.account_id.id
                index = 1
                for line in move_lines:
                    # line is a tuple (0, 0, {values})
                    if invoice_account_id == line[2]['account_id']:
                        line[2]['transaction_ref'] = u'{0}/{1:02d}'.format(
                            invoice.transaction_id, index)
                        index += 1
        return move_lines
