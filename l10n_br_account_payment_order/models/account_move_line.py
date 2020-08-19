# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants import ESTADOS_CNAB, SITUACAO_PAGAMENTO


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_scheduled = fields.Date(
        string='Data Prevista',
    )

    cnab_state = fields.Selection(
        selection=ESTADOS_CNAB,
        string='Estados CNAB',
        default='draft',
    )

    date_payment_created = fields.Date(
        string='Data da criação do pagamento',
        readonly=True,
    )

    own_number = fields.Char(
        string='Nosso Numero',
    )

    document_number = fields.Char(
        string='Número documento',
    )

    company_title_identification = fields.Char(
        string='Identificação Titulo Empresa',
    )

    payment_situation = fields.Selection(
        selection=SITUACAO_PAGAMENTO,
        string='Situação do Pagamento',
        default='inicial',
    )

    instructions = fields.Text(
        string='Instruções de cobrança',
        readonly=True,
    )

    residual = fields.Monetary(
        string='Valor Residual',
        default=0.0,
        currency_field='company_currency_id',
    )

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        vals['own_number'] = self.own_number
        vals['document_number'] = self.document_number
        vals['company_title_identification'] = self.company_title_identification

        if self.invoice_id.state == 'paid':
            vals['amount_currency'] = self.credit or self.debit

        return vals

    @api.multi
    def create_payment_line_from_move_line(self, payment_order):
        '''
        Altera estado do cnab para adicionado a ordem
        :param payment_order:
        :return:
        '''
        cnab_state = 'added'
        if self.invoice_id.state == 'paid':
            cnab_state = 'added_paid'

        self.cnab_state = cnab_state

        return super().create_payment_line_from_move_line(
            payment_order
        )

    @api.multi
    def generate_boleto(self, validate=True):
        raise NotImplementedError

    @api.multi
    def _update_check(self):

        if self._context.get('reprocessing'):
            return True

        return super(AccountMoveLine, self)._update_check()

    @api.multi
    def write(self, values):
        '''
        Sobrescrita do método Write. Não deve ser possível voltar o state_cnab
        ou a situacao_pagamento para um estado anterior
        :param values:
        :return:
        '''
        for record in self:
            state_cnab = values.get('state_cnab')

            if state_cnab and (
                record.state_cnab == 'done'
                or (
                    record.state_cnab in ['accepted', 'accepted_hml']
                    and state_cnab not in ['accepted', 'accepted_hml', 'done']
                )
            ):
                values.pop('state_cnab', False)

            if record.situacao_pagamento not in ['inicial', 'aberta']:
                values.pop('situacao_pagamento', False)

        return super().write(values)


    # journal_entry_ref = fields.Char(
    #     compute="_compute_journal_entry_ref", string="Journal Entry Ref", store=True
    # )
    #
    # @api.depends("move_id")
    # def _compute_journal_entry_ref(self):
    #     for record in self:
    #         if record.name:
    #             record.journal_entry_ref = record.name
    #         elif record.move_id.name:
    #             record.journal_entry_ref = record.move_id.name
    #         elif record.invoice_id and record.invoice_id.number:
    #             record.journal_entry_ref = record.invoice_id.number
    #         else:
    #             record.journal_entry_ref = "*" + str(record.move_id.id)

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
