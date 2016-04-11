# -*- coding: utf-8 -*-
##############################################################################
#
#    This module copyright (C) 2016 KMEE INFORMATICA LTDA
#           (<http://kmee.com.br>).
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
from decimal import Decimal
from openerp import models, api
from openerp.tools.float_utils import float_repr


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.model
    def get_possible_cnab_move_for_statement_line(self, this):
        """find orders that might be candidates for matching a statement
        line"""
        # verify that this ids are accessible to the user and from the
        domain = [('bank_title_name', '=', this.name),
                  ('cod_ocorrencia','=','6')]
        return self.env['l10n_br_cnab.move'].search(domain)

    @api.model
    def get_reconcile_lines_from_cnab_move(self, this, cnab_move, excluded_ids=None):
        """return lines to reconcile our statement line with"""
        move_lines = self.env['account.move.line']
        for cnab in cnab_move:
            move_lines += cnab.move_line_id
        move_lines.filtered(
            lambda record: record.transaction_ref == this.name)
        return self.env['account.move.line']\
            .prepare_move_lines_for_reconciliation_widget(move_lines)

    @api.model
    def get_reconciliation_proposition(self, this, excluded_ids=None):
        """See if we find a set payment order that matches our line. If yes,
        return all unreconciled lines from there"""
        cnab_move = self.get_possible_cnab_move_for_statement_line(this)
        if cnab_move:
            reconcile_lines = self.get_reconcile_lines_from_cnab_move(
                this, cnab_move, excluded_ids=None)
            if reconcile_lines:
                return reconcile_lines
        return super(AccountBankStatementLine, self)\
            .get_reconciliation_proposition(this, excluded_ids=excluded_ids)
