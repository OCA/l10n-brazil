# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants import ESTADOS_CNAB, SITUACAO_PAGAMENTO


class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ["account.move.line", "mail.thread", "mail.activity.mixin"]

    cnab_state = fields.Selection(
        selection=ESTADOS_CNAB,
        string='Estados CNAB',
        default='draft',
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

    # TODO - Mover seleção para o arquivo de Constantes,
    #  aguardando retorno para saber se existe diferença
    #  entre os Bancos, o CNAB 400 da Unicred e o 240 da
    #  Febraban v10.06 estão iguais, a seleção no arquivo
    #  de constantes está diferente.
    #  Caso exista diferença vai ser preciso fazer o mesmo
    #  que foi feito nos Codigos de Retorno
    movement_instruction_code = fields.Selection(
        string='Código da Instrução para Movimento',
        help='Campo G061 do CNAB',
        selection=[
            ('01', '01 - Remessa*'),
            ('02', '02 - Pedido de Baixa'),
            ('04', '04 - Concessão de Abatimento*'),
            ('05', '05 - Cancelamento de Abatimento'),
            ('06', '06 - Alteração de vencimento'),
            ('08', '08 - Alteração de Seu Número'),
            ('09', '09 - Protestar*'),
            ('11', '11 - Sustar Protesto e Manter em Carteira'),
            ('25', '25 - Sustar Protesto e Baixar Título'),
            ('26', '26 – Protesto automático'),
            ('31', '31 - Alteração de outros dados (Alteração de dados do pagador'),
            ('40', '40 - Alteração de Carteira')]
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

        # Codigo de Instrução do Movimento para Remessa
        vals['movement_instruction_code'] = self.movement_instruction_code

        if self.movement_instruction_code == '02':
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
