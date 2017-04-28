# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def define_account(self, move_line):
        amt = self.env['account.move.template']
        if move_line[2].tax_amount == 0:  # definir linha receita
            # definir parâmetros search
            amt = amt.search([('type', '=', 'receipt')])
            if move_line[2].debit:
                am = amt.debit_account_id
            else:
                am = amt.credit_account_id

        if False:  # definir linha impostopr
            amt = amt.search([]) #definir parâmetros search
            am = amt.debit_account_id

        return am or move_line['account_id']

    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)
        lines = list(move_lines)
        for move in lines:
            partida = move[2]
            move[2]['account_id'] = self.define_account(move[2])
            partida['debit'] = move[2]['credit']
            partida['credit'] = move[2]['debit']
            partida['account_id'] = self.define_account(partida)
            # FIXME: Ele considera apenas os lançamentos duplicados, mas no
            # caso de receita, tanto lançamento original quanto duplicado mudam
            # vide docs
            move_lines.append([0, 0, partida])
        return move_lines
