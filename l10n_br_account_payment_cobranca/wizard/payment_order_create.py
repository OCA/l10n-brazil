# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, api


class PaymentOrderCreate(models.TransientModel):
    _inherit = 'account.payment.line.create'

    # @api.multi
    # def extend_payment_order_domain(self, payment_order, domain):
    #     super(PaymentOrderCreate, self).extend_payment_order_domain(
    #         payment_order, domain)
    #
    #     if payment_order.mode.type.code == '240':
    #         if payment_order.mode.payment_order_type == 'cobranca':
    #             domain += [
    #                 ('debit', '>', 0)
    #             ]
    #
    #         # TODO: Refactor this
    #         if ('invoice.payment_mode_id', '=', False) in domain:
    #             domain.remove(('invoice.payment_mode_id', '=', False))
    #         if ('date_maturity', '<=', self.duedate) in domain:
    #             domain.remove(('date_maturity', '<=', self.duedate))
    #         if ('date_maturity', '=', False) in domain:
    #             domain.remove(('date_maturity', '=', False))
    #         if ('date_maturity', '<=', self.duedate) in domain:
    #             domain.remove(('date_maturity', '<=', self.duedate))
    #
    #     elif payment_order.mode.type.code == '400':
    #         if payment_order.mode.payment_order_type == 'cobranca':
    #             domain += [
    #                 ('debit', '>', 0),
    #                 ('account_id.type', '=', 'receivable'),
    #                 '&',
    #                 ('payment_mode_id', '=', payment_order.mode.id),
    #                 '&',
    #                 ('invoice.state', '=', 'open'),
    #                 ('invoice.fiscal_category_id.'
    #                  'property_journal.revenue_expense', '=', True)
    #             ]
    #         # TODO: Refactory this
    #         # TODO: domain do state da move_line.
    #         # index = domain.index(('invoice.payment_mode_id', '=', False))
    #         # del domain[index - 1]
    #         # domain.removemove(('invoice.payment_mode_id', '=', False))
    #         # index = domain.index(('date_maturity', '<=', self.duedate))
    #         # del domain[index - 1]
    #         # domain.remove(('date_maturity', '=', False))
    #         # domain.remove(('date_maturity', '<=', self.duedate))
    #
    #     elif payment_order.mode.type.code == '500':
    #         if payment_order.mode.payment_order_type == 'payment':
    #             domain += [
    #                 '&', ('credit', '>', 0),
    #                 ('account_id.type', '=', 'payable')
    #             ]
    #         # index = domain.index(('invoice.payment_mode_id', '=', False))
    #         # del domain[index - 1]
    #         # domain.remove(('invoice.payment_mode_id', '=', False))
    #         # index = domain.index(('date_maturity', '<=', self.duedate))
    #         # del domain[index - 1]
    #         # domain.remove(('date_maturity', '=', False))
    #         # domain.remove(('date_maturity', '<=', self.duedate))
    #
    #         index = domain.index(('account_id.type', '=', 'receivable'))
    #         del domain[index - 1]
    #         domain.remove(('account_id.type', '=', 'receivable'))
    #
    #     return True
    #
    # @api.multi
    # def _prepare_payment_line(self, payment, line):
    #     res = super(PaymentOrderCreate, self)._prepare_payment_line(
    #         payment, line)
    #
    #     # res['communication2'] = line.payment_mode_id.comunicacao_2
    #     res['percent_interest'] = line.payment_mode_id.cnab_percent_interest
    #
    #     if payment.mode.type.code == '400':
    #         # write bool to move_line to avoid it being added on cnab again
    #         self.write_cnab_rejected_bool(line)
    #
    #     return res
    #
    # @api.multi
    # def filter_lines(self, lines):
    #     """ Filter move lines before proposing them for inclusion
    #         in the payment order.
    #
    #     This implementation filters out move lines that are already
    #     included in draft or open payment orders. This prevents the
    #     user to include the same line in two different open payment
    #     orders. When the payment order is sent, it is assumed that
    #     the move will be reconciled soon (or immediately with
    #     account_banking_payment_transfer), so it will not be
    #     proposed anymore for payment.
    #
    #     See also https://github.com/OCA/bank-payment/issues/93.
    #
    #     :param lines: recordset of move lines
    #     :returns: list of move line ids
    #     """
    #
    #     self.ensure_one()
    #     payment_lines = self.env['payment.line']. \
    #         search([('order_id.state', 'in', ('draft', 'open', 'done')),
    #                 ('move_line_id', 'in', lines.ids)])
    #     # Se foi exportada e o cnab_rejeitado dela for true, pode adicionar
    #     # de novo
    #     to_exclude = set([l.move_line_id.id for l in payment_lines
    #                       if not l.move_line_id.is_cnab_rejected])
    #     return [l.id for l in lines if l.id not in to_exclude]
    #
    # @api.multi
    # def write_cnab_rejected_bool(self, line):
    #     line.write({'is_cnab_rejected': False})
    #

    @api.multi
    def _prepare_move_line_domain(self):
        """ Nenhuma linha deve ser adicionada novamente a nao ser que o
        retorno do cnab informe que o registro falhou

        :return:
        """
        domain = super(PaymentOrderCreate, self)._prepare_move_line_domain()

        paylines = self.env['account.payment.line'].search([
            ('state', 'in', ('draft', 'open', 'generated', 'uploaded')),
            ('move_line_id', '!=', False)])

        if paylines:
            move_lines_ids = [
                payline.move_line_id.id for payline in paylines
                if not payline.move_line_id.is_cnab_rejected
            ]
            domain += [('id', 'not in', move_lines_ids)]

        return domain