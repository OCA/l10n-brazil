# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants import ESTADOS_CNAB, SITUACAO_PAGAMENTO


class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ["account.move.line", "mail.thread", "mail.activity.mixin"]

    # TODO - possível tornar um compute ?
    cnab_state = fields.Selection(
        selection=ESTADOS_CNAB,
        string='Estados CNAB',
        default='draft',
    )

    own_number = fields.Char(
        string='Nosso Numero',
    )

    # No arquivo de retorno do CNAB o campo pode ter um tamanho diferente,
    # o tamanho do campo é preenchido na totalidade com zeros a esquerda,
    # e no odoo o tamanho do sequencial pode estar diferente
    # ex.: retorno cnab 0000000000000201 own_number 0000000201
    # o campo abaixo foi a forma que encontrei para poder usar o
    # nosso_numero_cnab_retorno.strip("0") e ter algo:
    #  ex.: retorno cnab 201 own_number_without_zfill 201
    # Assim o metodo que faz o retorno do CNAB consegue encontrar
    # a move line relacionada ao Evento.
    own_number_without_zfill = fields.Char(
        compute='_compute_own_number_without_zfill',
        store=True, copy=False,
    )

    # Podem existir sequencias do nosso numero/own_number iguais entre bancos
    # diferentes, porém o Diario/account.journal não pode ser o mesmo.
    journal_payment_mode_id = fields.Many2one(
        comodel_name='account.journal',
        compute='_compute_journal_payment_mode',
        store=True, copy=False
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
        track_visibility='onchange',
    )

    instructions = fields.Text(
        string='Instruções de cobrança',
        readonly=True,
    )

    journal_entry_ref = fields.Char(
        string="Journal Entry Ref",
        compute="_compute_journal_entry_ref",
        store=True,
    )
    payment_mode_id = fields.Many2one(
        track_visibility='onchange'
    )
    date_maturity = fields.Date(
        readonly=True,
        track_visibility='onchange'
    )
    last_change_reason = fields.Text(
        readonly=True,
        track_visibility='onchange',
        string="Justificativa",
    )

    mov_instruction_code_id = fields.Many2one(
        comodel_name='l10n_br_cnab.mov.instruction.code',
        string='Código da Instrução para Movimento',
        help='Campo G061 do CNAB',
    )

    # Usados para deixar invisiveis/somente leitura
    # os campos relacionados ao CNAB
    payment_method_id = fields.Many2one(
        comodel_name='account.payment.method',
        related='payment_mode_id.payment_method_id',
        string='Payment Method',
    )

    payment_method_code = fields.Char(
        related='payment_method_id.code',
        readonly=True, store=True,
        string='Payment Method Code'
    )

    @api.depends("move_id")
    def _compute_journal_entry_ref(self):
        for record in self:
            if record.name:
                record.journal_entry_ref = record.name
            elif record.move_id.name:
                record.journal_entry_ref = record.move_id.name
            elif record.invoice_id and record.invoice_id.number:
                record.journal_entry_ref = record.invoice_id.number
            else:
                record.journal_entry_ref = "*" + str(record.move_id.id)

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        vals['own_number'] = self.own_number
        vals['document_number'] = self.document_number
        vals['company_title_identification'] = self.company_title_identification

        vals['payment_mode_id'] = self.payment_mode_id.id

        # Codigo de Instrução do Movimento para Remessa
        vals['mov_instruction_code_id'] = self.mov_instruction_code_id.id

        # Se for uma solicitação de baixa do título é preciso informar o
        # campo debit o codigo original coloca o amount_residual
        if self.mov_instruction_code_id.id ==\
                self.payment_mode_id.cnab_write_off_code_id.id:
            vals['amount_currency'] = self.credit or self.debit

        # TODO - ainda necessário ?
        # if self.invoice_id.state == 'paid':
        #    vals['amount_currency'] = self.credit or self.debit

        return vals

    @api.multi
    def create_payment_line_from_move_line(self, payment_order):
        """
        Altera estado do cnab para adicionado a ordem
        :param payment_order:
        :return:
        """
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
        """
        Sobrescrita do método Write. Não deve ser possível voltar o cnab_state
        ou a situacao_pagamento para um estado anterior
        :param values:
        :return:
        """
        for record in self:
            cnab_state = values.get('cnab_state')

            if cnab_state and (
                record.cnab_state == 'done'
                or (
                    record.cnab_state in ['accepted', 'accepted_hml']
                    and cnab_state not in ['accepted', 'accepted_hml', 'done']
                )
            ):
                values.pop('cnab_state', False)

            if record.payment_situation not in ['inicial', 'aberta']:
                values.pop('payment_situation', False)

        return super().write(values)

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

    def _create_payment_order_change(self, **kwargs):
        self.ensure_one()
        # TODO:

    def _change_date_maturity(self, new_date, reason, **kwargs):
        moves_to_sync = self.filtered(lambda m: m.date_maturity != new_date)
        moves_to_sync._create_payment_order_change(new_date=new_date, **kwargs)
        moves_to_sync.write({
            'date_maturity': new_date,
            'last_change_reason': reason,
        })

    def _change_payment_mode(self, reason, new_payment_mode_id, **kwargs):
        moves_to_sync = self.filtered(
            lambda m: m.payment_mode_id != new_payment_mode_id)
        moves_to_sync._create_payment_order_change(
            new_payment_mode_id=new_payment_mode_id, **kwargs)
        moves_to_sync.write({
            'payment_mode_id': new_payment_mode_id.id,
            'last_change_reason': reason,
        })

    def _create_baixa(self, reason, **kwargs):
        moves_to_sync = self.filtered(lambda m: True)
        # TODO: Verificar restrições possíveis
        moves_to_sync._create_payment_order_change(baixa=True, **kwargs)
        moves_to_sync.write({
            'last_change_reason': reason,
            'payment_situation': 'baixa',  # FIXME: Podem ser múltiplos motivos
        })

    def _create_change(self, change_type, reason='', **kwargs):
        if change_type == 'change_date_maturity':
            self._change_date_maturity(reason, **kwargs)
        elif change_type == 'change_payment_mode':
            self._change_payment_mode(reason, **kwargs)
        elif change_type == 'baixa':
            self._create_baixa(reason, **kwargs)

    @api.multi
    @api.depends('own_number')
    def _compute_own_number_without_zfill(self):
        for record in self:
            if record.own_number:
                record.own_number_without_zfill = record.own_number.strip('0')

    @api.multi
    @api.depends('payment_mode_id')
    def _compute_journal_payment_mode(self):
        for record in self:
            if record.payment_mode_id:
                # CNAB usa sempre a opção fixed_journal_id
                if record.payment_mode_id.fixed_journal_id:
                    record.journal_payment_mode_id =\
                        record.payment_mode_id.fixed_journal_id.id
