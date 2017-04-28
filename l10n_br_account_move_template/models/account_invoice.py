# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def define_account(self, move_line, type):
        """
        Definir contas das novas partidas de acordo com o roteiro contabil
        :param move_line:  - dict - partida duplicada para contra-partida
                                    na conta contabil
        :param type: sting - Tipo de partida ['CLIENTE', 'RECEITA', 'IMPOSTO']
        :return:
        """
        amt = self.env['account.move.template']
        if type == 'CLIENTE':
            # definir parâmetros search
            amt = amt.search([('type', '=', 'receipt')])

            if move_line[2].debit:
                account_id = amt.debit_account_id
            else:
                account_id = amt.credit_account_id

        elif type == 'IMPOSTO':
            amt = amt.search([]) #definir parâmetros search
            account_id = amt.debit_account_id

        # Se definir uma conta no mapeamento, seta a conta,
        # senão fica com a conta padrão
        if account_id:
            move_line['account_id'] = account_id

    def finalize_invoice_move_lines(self, move_lines):
        """
        Sobrescrever hook do core para criar as contrapartidas de acordo com
        o tipo da partida e mapear as contas seguindo o roteiro contábil.
        :param move_lines: lista com [0,0, dict] - Move lines geradas pelo core
        :return: - lista com [0,0, dict] onde o dict são as partidas a serem 
                                         criadas para o lançamento contabil
                                         da invoice.
        """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)
        lines = list(move_lines)
        for move in lines:
            if move[2].get('product_id', False):
                type =  'RECEITA'
                move_lines.remove(move)

            elif move[2].get('tax_amount', False):
                type =  'IMPOSTO'

            else:
                type = 'CLIENTE'

            # Criar contra-partidas
            if type in ['IMPOSTO', 'CLIENTE']:
                partida = dict(move[2])
                partida['name'] = 'Contrapartida - ' + move[2]['name']
                move[2]['account_id'] = 30
                partida['debit'] = move[2]['credit']
                partida['credit'] = move[2]['debit']
                move_lines.append([0, 0, partida])
                # self.define_account(move, type)

        return move_lines
