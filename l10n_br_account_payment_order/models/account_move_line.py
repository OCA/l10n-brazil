# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_scheduled = fields.Date(string='Data Prevista')

    @api.depends('move_id')
    def _compute_journal_entry_ref(self):
        for record in self:
            if record.name:
                record.journal_entry_ref = record.name
            elif record.move_id.name:
                record.journal_entry_ref = record.move_id.name
            elif record.invoice_id and record.invoice_id.number:
                record.journal_entry_ref = record.invoice_id.number
            else:
                record.journal_entry_ref = '*' + str(record.move_id.id)

    journal_entry_ref = fields.Char(
        compute='_compute_journal_entry_ref',
        string='Journal Entry Ref', store=True)

    @api.multi
    def get_balance(self):
        """
        Return the balance of any set of move lines.

        Not to be confused with the 'balance' field on this model, which
        returns the account balance that the move line applies to.
        """
        total = 0.0
        for line in self:
            total += (line.debit or 0.0) - (line.credit or 0.0)
        return total
