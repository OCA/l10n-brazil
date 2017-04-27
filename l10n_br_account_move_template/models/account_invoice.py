# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


# HARD_IMPOSTO = 30
#
# class AccountTax(models.Model):
#     _inherit = 'account.tax'

    # @api.model
    # def _unit_compute(
    #         self, taxes, price_unit, product=None, partner=None, quantity=0):
    #     data = super(AccountTax, self)._unit_compute(
    #         taxes, price_unit, product, partner, quantity)
    #     for dict in data:
    #         if 'id' in dict:
    #             tax = self.browse(dict['id'])
    #             if tax:
    #                 # FIXME: Chamar os roteiros contabeis e determinar a conta
    #                 dict.update({
    #                     'account_counterpart_id': HARD_IMPOSTO,
    #                 })
    #     return data


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def define_account(self, move_line):
        amt = self.env['account.move.template']
        am = self.env['account.account']
        if move_line[2].tax_amount == 0:  # definir linha receita
            # definir parâmetros search
            amt = amt.search([('type', '=', 'receipt')])
            if move_line[2].debit:
                am = amt.debit_account_id or move_line[2].partner_id.\
                    property_account_receivable
            else:
                am = amt.credit_account_id or move_line[2].product_id.\
                    property_account_income

        if False:  # definir linha imposto
            amt = amt.search([]) #definir parâmetros search

        return am

    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(
            move_lines)
        lines = list(move_lines)
        for move in lines:
            partida = move[2]
            aux_debit = partida['debit']
            partida['debit'] = partida['credit']
            partida['credit'] = aux_debit
            partida['account_id'] = self.define_account(move)
            # FIXME: Ele considera apenas os lançamentos duplicados, mas no
            # caso de receita, tanto lançamento original quanto duplicado mudam
            # vide docs
            move_lines.append([0, 0, partida])
        return move_lines
