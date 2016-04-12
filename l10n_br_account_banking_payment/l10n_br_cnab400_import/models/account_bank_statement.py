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
from openerp import models, api, _
from openerp.tools.float_utils import float_repr
from openerp.exceptions import Warning as UserError


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.model
    def get_reconcile_lines_from_cnab_move(self, this, excluded_ids=None):
        """return move.line to reconcile with statement line"""
        move_lines = self.env['account.move.line'].search(
                [('transaction_ref', '=', this.name),
                 ('name', '=', this.ref)
                 ])
        try:
            assert len(move_lines) <= 1
        except:
            raise UserError(_(
                        "Erro!\n "
                        "Nosso numero duplicado"
                    ))
        return self.env['account.move.line']\
            .prepare_move_lines_for_reconciliation_widget(move_lines)

    @api.model
    def get_reconciliation_proposition(self, this, excluded_ids=None):
        """See if we find a set payment order that matches our line. If yes,
        return all unreconciled lines from there"""

        reconcile_lines = self.get_reconcile_lines_from_cnab_move(
            this, excluded_ids=None)
        if reconcile_lines:
            return reconcile_lines
        elif this.bank_account_id.state == "cnab":
            return []
        else:
            return super(AccountBankStatementLine, self)\
              .get_reconciliation_proposition(this, excluded_ids=excluded_ids)
