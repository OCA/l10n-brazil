# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_scheduled = fields.Date(string='Data Prevista')

    # TODO: Verificar informação ref a numeração na localização brasileira
    @api.one
    def _get_journal_entry_ref(self):
        if self.move_id.state == 'draft':
            if self.invoice.id:
                self.journal_entry_ref = self.invoice.number
            else:
                self.journal_entry_ref = '*' + str(self.move_id.id)
        else:
            self.journal_entry_ref = self.move_id.name

    journal_entry_ref = fields.Char(compute=_get_journal_entry_ref,
                                    string='Journal Entry Ref')

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

    # TODO: Criar metodos para implementação de juros e outros
        # detalhes pertinentes.
