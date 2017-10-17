# -*- coding: utf-8 -*-
# ###########################################################################
#
#    Author: Luis Felipe Mileo
#            Fernando Marcato Rodrigues
#            Daniel Sadamo Hirayama
#    Copyright 2015 KMEE - www.kmee.com.br
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


from openerp import models, api


class PaymentOrderCreate(models.TransientModel):
    _inherit = 'payment.order.create'

    @api.multi
    def extend_payment_order_domain(self, payment_order, domain):
        super(PaymentOrderCreate, self).extend_payment_order_domain(
            payment_order, domain)

        if payment_order.mode.type.code == '240':
            if payment_order.mode.payment_order_type == 'cobranca':
                domain += [
                    ('debit', '>', 0)
                ]

            # TODO: Refactor this
            if ('invoice.payment_mode_id', '=', False) in domain:
                domain.remove(('invoice.payment_mode_id', '=', False))
            if ('date_maturity', '<=', self.duedate) in domain:
                domain.remove(('date_maturity', '<=', self.duedate))
            if ('date_maturity', '=', False) in domain:
                domain.remove(('date_maturity', '=', False))
            if ('date_maturity', '<=', self.duedate) in domain:
                domain.remove(('date_maturity', '<=', self.duedate))

        elif payment_order.mode.type.code == '400':
            if payment_order.mode.payment_order_type == 'cobranca':
                domain += [
                    ('debit', '>', 0),
                    ('account_id.type', '=', 'receivable'),
                    '&',
                    ('payment_mode_id', '=', payment_order.mode.id),
                    '&',
                    ('invoice.state', '=', 'open'),
                    ('invoice.fiscal_category_id.'
                     'property_journal.revenue_expense', '=', True)
                ]
            # TODO: Refactory this
            # TODO: domain do state da move_line.
            # index = domain.index(('invoice.payment_mode_id', '=', False))
            # del domain[index - 1]
            # domain.removemove(('invoice.payment_mode_id', '=', False))
            # index = domain.index(('date_maturity', '<=', self.duedate))
            # del domain[index - 1]
            # domain.remove(('date_maturity', '=', False))
            # domain.remove(('date_maturity', '<=', self.duedate))

        elif payment_order.mode.type.code == '500':
            if payment_order.mode.payment_order_type == 'payment':
                domain += [
                    '&', ('credit', '>', 0),
                    ('account_id.type', '=', 'payable')
                ]
            # index = domain.index(('invoice.payment_mode_id', '=', False))
            # del domain[index - 1]
            # domain.remove(('invoice.payment_mode_id', '=', False))
            # index = domain.index(('date_maturity', '<=', self.duedate))
            # del domain[index - 1]
            # domain.remove(('date_maturity', '=', False))
            # domain.remove(('date_maturity', '<=', self.duedate))

            index = domain.index(('account_id.type', '=', 'receivable'))
            del domain[index - 1]
            domain.remove(('account_id.type', '=', 'receivable'))

        return True

    @api.multi
    def _prepare_payment_line(self, payment, line):
        res = super(PaymentOrderCreate, self)._prepare_payment_line(
            payment, line)

        # res['communication2'] = line.payment_mode_id.comunicacao_2
        res['percent_interest'] = line.payment_mode_id.cnab_percent_interest

        if payment.mode.type.code == '400':
            # write bool to move_line to avoid it being added on cnab again
            self.write_cnab_rejected_bool(line)

        return res

    @api.multi
    def filter_lines(self, lines):
        """ Filter move lines before proposing them for inclusion
            in the payment order.

        This implementation filters out move lines that are already
        included in draft or open payment orders. This prevents the
        user to include the same line in two different open payment
        orders. When the payment order is sent, it is assumed that
        the move will be reconciled soon (or immediately with
        account_banking_payment_transfer), so it will not be
        proposed anymore for payment.

        See also https://github.com/OCA/bank-payment/issues/93.

        :param lines: recordset of move lines
        :returns: list of move line ids
        """

        self.ensure_one()
        payment_lines = self.env['payment.line'].\
            search([('order_id.state', 'in', ('draft', 'open', 'done')),
                    ('move_line_id', 'in', lines.ids)])
        # Se foi exportada e o cnab_rejeitado dela for true, pode adicionar
        # de novo
        to_exclude = set([l.move_line_id.id for l in payment_lines
                          if not l.move_line_id.is_cnab_rejected])
        return [l.id for l in lines if l.id not in to_exclude]

    @api.multi
    def write_cnab_rejected_bool(self, line):
        line.write({'is_cnab_rejected': False})
