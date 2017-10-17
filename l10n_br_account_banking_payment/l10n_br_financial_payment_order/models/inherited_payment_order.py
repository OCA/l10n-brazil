# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import models, fields, api, exceptions, workflow, _
from openerp.exceptions import ValidationError
# from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import TIPO_DE_FOLHA
from openerp.addons.financial.constants import (
    FINANCIAL_DEBT_2RECEIVE,
    FINANCIAL_DEBT_2PAY,
)
from ..constantes import (
    TIPO_ORDEM_PAGAMENTO,
    TIPO_ORDEM_PAGAMENTO_BOLETO,
    TIPO_ORDEM_PAGAMENTO_PAGAMENTO,
)


class PaymentOrder(models.Model):

    _name = b'payment.order'
    _inherit = ['payment.order', 'mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('mode.nivel_aprovacao')
    def _compute_nivel_aprovacao(self):
        for record in self:
            record.nivel_aprovacao = int(record.mode.nivel_aprovacao)

    @api.multi
    @api.depends('mode.tipo_pagamento')
    def _compute_financial_type(self):
        for record in self:
            if record.mode.tipo_pagamento == TIPO_ORDEM_PAGAMENTO_BOLETO:
                record.financial_type = FINANCIAL_DEBT_2RECEIVE
            else:
                record.financial_type = FINANCIAL_DEBT_2PAY

    state = fields.Selection(
        selection=[
            ('draft', 'Rascunho'),
            ('waiting', 'Aguardando aprovação'),
            ('waiting2', 'Aguardando segunda aprovação'),
            ('open', 'Confirmado'),
            ('generated', 'Arquivo gerado'),
            ('done', 'Arquivo enviado ao banco'),  # v10: uploaded
            ('cancel', 'Cancel'),
        ],
        string='Status',
        readonly=True,
        copy=False,
        default='draft',
        track_visibility='onchange',
    )
    tipo_pagamento = fields.Selection(
        string="Tipos de Ordem de Pagamento",
        selection=TIPO_ORDEM_PAGAMENTO,
        help="Tipos de Ordens de Pagamento.",
        states={'done': [('readonly', True)]},
    )
    tipo_exportacao = fields.Char(
        string='Tipo de exportação',
        related='mode.type.code',
        size=64,
        readonly=True,
    )
    search_date_start = fields.Date(
        string="De",
        states={'draft': [('readonly', False)]},
    )
    search_date_stop = fields.Date(
        string="Até",
        states={'draft': [('readonly', False)]},
    )
    search_date_type = fields.Selection(
        selection=[
            ('date_document', 'Documento'),
            ('date_maturity', 'Vencimento'),
            ('date_business_maturity', 'Vencimento útil'),
            ('date_payment', 'Pagamento'),
        ],
        string="Data",
        states={'draft': [('readonly', False)]},
    )
    search_financial_document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Tipo de documento'
    )
    nivel_aprovacao = fields.Integer(
        compute='_compute_nivel_aprovacao',

    )
    financial_type = fields.Selection(
        selection=[
            (FINANCIAL_DEBT_2RECEIVE,'A receber'),
            (FINANCIAL_DEBT_2PAY, 'A pagar'),
         ],
        compute='_compute_financial_type',
    )

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
        communication = line.document_number or '-'
        # communication = line.ref or '-'
        # TODO:
        # - Implementar novamente o campo ref? Pois o display name pode
        # ser alterado
        # - Como devemos lidar com um deposito identificado?
        # - Podemos inserir com uma moeda diferente da ordem de pagamento?
        #

        amount_currency = line.amount_residual

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

        if self.search_date_start:
            domain += [
                (self.search_date_type, '>=', self.search_date_start),
            ]
        if self.search_date_stop:
            domain += [
                (self.search_date_type, '<=', self.search_date_stop),
            ]
        if self.search_financial_document_type_id:
            domain += [
                ('document_type_id', '=',
                 self.search_financial_document_type_id.id),
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
        """ A importação de lançamentos financeiros nas payment orders
        funciona da seguinte maneira:

        1. Prepara o dominio de busca: extend_payment_order_domain
        2. Realiza a busca
        3. Filtrar os registros já inseridos em payment.orders:
            filter_financial_lines
        4. Preparar: Prepara os dados para inclusão:
            _prepare_financial_payment_line
        5. Criar

        :return:
        """

        self.line_ids.unlink()

        domain = []

        self.extend_payment_order_domain(domain)
        lines = self.env['financial.move'].search(domain)
        filtered_lines = self.filter_financial_lines(lines)

        for line in filtered_lines:
            vals = self._prepare_financial_payment_line(line)
            self.line_ids.create(vals)

        return

    @api.multi
    def gera_financeiro_remessa(self):
        for record in self:
            if len(record.line_ids) == 1:
                partner = record.line_ids[0].partner_id
            else:
                partner = record.company_id.partner_id

            date = record.date_scheduled

            dados = {
                'date_document': record.date_done,
                'partner_id': partner.id,
                'company_id': record.company_id.id,
                'doc_source_id': 'payment.order,' + str(record.id),
                'currency_id': record.company_id.currency_id.id,
                # 'payment_order_id': record.id,
                'document_type_id':
                    record.mode.remessa_document_type_id.id,
                'account_id': record.mode.remessa_financial_account_id.id,
                'date_maturity': date,
                'amount_document': record.total,
                'document_number':
                    '{0.name}-{1.reference}-({2})'.format(
                        record.mode, record,
                        unicode(len(record.line_ids))),
                'payment_mode_id': record.mode.id,
                'type': record.financial_type,
            }

            finacial_move_id = self.env['financial.move'].create(dados)
            # TODO: Melhorar este metodo!

    @api.multi
    def action_done(self):
        result = super(PaymentOrder, self).action_done()
        
        # for record in self:
        #     if record.state == 'done' and record.mode.gera_financeiro_remessa:
        #         record.gera_financeiro_remessa()
        return True

    @api.multi
    def launch_wizard(self):
        """Search for a wizard to launch according to the type.
        If type is manual. just confirm the order.
        Previously (pre-v6) in account_payment/wizard/wizard_pay.py
        """
        context = self.env.context.copy()
        order = self[0]
        # check if a wizard is defined for the first order
        if order.mode.type and order.mode.type.ir_model_id:
            context['active_ids'] = self.ids
            wizard_model = order.mode.type.ir_model_id.model
            wizard_obj = self.env[wizard_model]
            return {
                'name': wizard_obj._description or _('Payment Order Export'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': wizard_model,
                'domain': [],
                'context': context,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'nodestroy': True,
            }
        else:
            # should all be manual orders without type or wizard model
            for order in self[1:]:
                if order.mode.type and order.mode.type.ir_model_id:
                    raise exceptions.Warning(
                        _('Error'),
                        _('You can only combine payment orders of the same '
                          'type'))
            # process manual payments
            for order_id in self.ids:
                workflow.trg_validate(self.env.uid, 'payment.order',
                                      order_id, 'generated', self.env.cr)
            return {}

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
