# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 - KMEE INFORMATICA LTDA (<http://kmee.com.br>).
#              Luis Felipe Miléo - mileo@kmee.com.br
#
#    All other contributions are (C) by their respective contributors
#
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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