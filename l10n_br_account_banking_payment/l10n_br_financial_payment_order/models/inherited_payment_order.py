# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
# from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import TIPO_DE_FOLHA
from openerp.addons.financial.constants import (
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_DEBT_2PAY,
)
from ..constantes import (
    TIPO_ORDEM_PAGAMENTO,
    TIPO_ORDEM_PAGAMENTO_BOLETO,
    TIPO_ORDEM_PAGAMENTO_PAGAMENTO
)


class PaymentOrder(models.Model):

    _inherit = b'payment.order'

    tipo_pagamento = fields.Selection(
        string="Tipos de Ordem de Pagamento",
        selection=TIPO_ORDEM_PAGAMENTO,
        help="Tipos de Ordens de Pagamento.",
        states={'done': [('readonly', True)]},
    )
    search_date_start = fields.Date(
        string="De",
        states={'done': [('readonly', True)]},
    )
    search_date_stop = fields.Date(
        string="Até",
        states={'done': [('readonly', True)]},
    )
    search_date_type = fields.Selection(
        selection=[
            ('date_document', 'Documento'),
            ('date_maturity', 'Vencimento'),
            ('date_business_maturity', 'Vencimento útil'),
            ('date_payment', 'Pagamento'),
        ],
        default='date_document',
        string="Data",
        states={'done': [('readonly', True)]},
    )
    # tipo_de_folha = fields.Selection(
    #     selection=TIPO_DE_FOLHA,
    #     string=u'Tipo de folha',
    #     default='normal',
    #     states={'done': [('readonly', True)]},

    @api.multi
    def action_open(self):
        """
        Validacao ao confirmar ordem:
        """
        for record in self:
            if not record.line_ids:
                raise ValidationError(
                    _("Impossivel confirmar linha vazia!"))
        res = super(PaymentOrder, self).action_open()
        return res

    @api.multi
    def cancel(self):
        for line in self.line_ids:
            if line.payslip_id:
                line.write({'payslip_id': ''})
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def _prepare_financial_payment_line(self, line):
        """This function is designed to be inherited
        The resulting dict is passed to the create method of payment.line"""

        self.ensure_one()
        _today = fields.Date.context_today(self)
        date_to_pay = False  # no payment date => immediate payment

        if self.date_prefered == 'due':
            #
            # Caso a data preferida seja a data de vencimento
            #

            #
            # TODO: Verificar o que fazer com lançamentos vencidos
            #

            date_to_pay = (
                line.date_maturity
                if line.date_maturity and line.date_maturity > _today
                else False)

        elif self.date_prefered == 'fixed':
            #
            # Caso da data preferida seja uma data fixa e esta data seja maior
            # que a data de hoje.
            #
            date_to_pay = (
                self.date_scheduled
                if self.date_scheduled and self.date_scheduled > _today
                else False)

        state = 'normal'
        communication = line.display_name or '-'
        # communication = line.ref or '-'
        # TODO:
        # - Implementar novamente o campo ref? Pois o display name pode
        # ser alterado
        # - Como devemos lidar com um deposito identificado?
        # - Podemos inserir com uma moeda diferente da ordem de pagamento?
        #

        amount_currency = line.amount_document

        # TODO: Devemos expressar o valor com sinal negativo em alguns casos?
        # if self.payment_order_type == 'debit':
        #     amount_currency *= -1
        #

        #
        # Método para buscar a conta bancária aplicável a operação:
        # - Exemplo de um caso de uso possível:
        #         - O funcionário tem 2 contas, mas ao receber o seu salário,
        #       o valor deve ser depositado na conta salário

        # line2bank = line.line2bank(self.mode.id)

        res = {
            'financial_id': line.id,
            'amount_currency': amount_currency,
            # 'bank_id': line2bank.get(line.id),
            'order_id': self.id,
            'partner_id': line.partner_id and line.partner_id.id or False,
            'communication': communication,
            'state': state,
            'date': date_to_pay,
            'currency': (line.currency_id and line.currency_id.id or
                    line.journal_id.currency.id or
                    line.journal_id.company_id.currency_id.id)
        }
        return res

    @api.multi
    def filter_financial_lines(self, lines):
        """ Filter move lines before proposing them for inclusion
            in the payment order.

        This implementation filters out financial lines that are already
        included in draft or open payment orders. This prevents the
        user to include the same line in two different open payment
        orders.

        See also https://github.com/OCA/bank-payment/issues/93.

        :param lines: recordset of move lines
        :returns: list of move line ids
        """
        self.ensure_one()
        to_exclude = self.env['payment.line']. \
            search([('order_id.state', 'in', ('draft', 'open')),
                    ('financial_id', 'in', lines.ids)]).mapped('financial_id')

        # TODO: Verificar quando podemos incluir duas vezes um financial_move.

        return lines - to_exclude

    @api.multi
    def extend_payment_order_domain(self, domain):
        self.ensure_one()

        domain += [
            ('company_id', '=', self.company_id.id),
            # ('amount_residual', '>', 0), # FIXME
        ]

        if self.mode.tipo_pagamento == TIPO_ORDEM_PAGAMENTO_BOLETO:
            domain += [
                ('payment_mode_id', '=', self.mode.id),
                ('type', '=', FINANCIAL_DEBT_2RECEIVE),
            ]
        elif self.mode.tipo_pagamento == TIPO_ORDEM_PAGAMENTO_PAGAMENTO:
            domain += [
                ('type', '=', FINANCIAL_DEBT_2PAY),
            ]
        else:
            raise NotImplemented

    @api.one
    def financial_payment_import(self):
        """
        1. Buscar
        2. Extender
        3. Filtrar
        4. Preparar
        5. Criar

        :return:
        """
        payment_line_obj = self.env['payment.line']

        domain = []

        self.extend_payment_order_domain(domain)
        lines = self.env['financial.move'].search(domain)
        filtered_lines = self.filter_financial_lines(lines)

        for line in filtered_lines:
            vals = self._prepare_financial_payment_line(line)
            payment_line_obj.create(vals)

        return


    @api.multi
    def buscar_holerites_wizard(self):
        context = dict(self.env.context)
        context.update({
            'active_id': self.id,
        })
        form = self.env.ref(
            'l10n_br_financial_payment_order.'
            'payslip_payment_create_order_view',
            True
        )
        return {
            'view_type': 'form',
            'view_id': [form.id],
            'view_mode': 'form',
            'res_model': 'payslip.payment.order.created',
            'views': [(form.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
