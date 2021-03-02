# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..constants import ESTADOS_CNAB, SITUACAO_PAGAMENTO


class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ['account.move.line', 'mail.thread']
    # As linhas de cobrança precisam ser criadas conforme sequencia de
    # Data de Vencimentos/date_maturity senão ficam fora de ordem:
    #  ex.: own_number 201 31/12/2020, own_number 202 18/11/2020
    #  Isso causa confusão pois a primeira parcela fica como sendo a segunda.
    _order = 'date desc, date_maturity ASC, id desc'

    # TODO - possível tornar um compute ?
    cnab_state = fields.Selection(
        selection=ESTADOS_CNAB,
        string='Estados CNAB',
        default='draft',
    )

    own_number = fields.Char(
        string='Nosso Numero',
        track_visibility='onchange',
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
        track_visibility='onchange',
    )

    company_title_identification = fields.Char(
        string='Identificação Titulo Empresa',
        track_visibility='onchange',
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
        track_visibility='onchange',
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

    def _get_payment_order(self, invoice):
        """
        Obtem a Ordem de Pagamento a ser usada e se é uma nova
        :param invoice:
        :return: Orderm de Pagamento, E se é uma nova
        """

        # Verificar Ordem de Pagto
        apo = self.env['account.payment.order']
        # Existe a possibilidade de uma Fatura ter diferentes
        # Modos de Pagto nas linhas no caso CNAB ?
        payorder = apo.search([
            ('payment_mode_id', '=', invoice.payment_mode_id.id),
            ('state', '=', 'draft')], limit=1)
        new_payorder = False
        if not payorder:
            payorder = apo.create(
                invoice._prepare_new_payment_order(invoice.payment_mode_id)
            )
            new_payorder = True

        return payorder, new_payorder

    def _check_cnab_instruction_to_be_send(self):
        """
        CNAB - Não pode ser enviada uma Instrução
         de CNAB se houver uma pendente.
        :return: Mensagem de Erro caso exista
        """
        payment_line_to_be_send = self.payment_line_ids.filtered(
            lambda t: t.order_id.state in ('draft', 'open', 'generated'))
        if payment_line_to_be_send:
            raise UserError(_(
                'There is a CNAB Payment Order %s in status %s'
                ' related to invoice %s created, the CNAB file'
                ' should be sent to bank, because only after'
                ' that it is possible make another CNAB Instruction.'
            ) % (payment_line_to_be_send.order_id.name,
                 payment_line_to_be_send.order_id.state, self.invoice_id.number))
        pass

    def _msg_cnab_payment_order_at_invoice(self, new_payorder, payorder):
        """
        CNAB - Registra a mensagem de alteração na Fatura para rastreabilidade.
        :param new_payorder: Se é uma nova Ordem de Pagamento/Debito
        :param payorder: Objeto Ordem de Pagamento/Debito
        :return:
        """

        cnab_instruction = self.mov_instruction_code_id.code + ' - ' + \
                           self.mov_instruction_code_id.name
        if new_payorder:
            self.invoice_id.message_post(body=_(
                'Payment line added to the the new draft payment '
                'order %s which has been automatically created,'
                ' to send CNAB Instruction %s for OWN NUMBER %s.'
            ) % (payorder.name, cnab_instruction, self.own_number))
        else:
            self.invoice_id.message_post(body=_(
                'Payment line added to the existing draft '
                'order %s to send CNAB Instruction %s for OWN NUMBER %s.'
            ) % (payorder.name, cnab_instruction, self.own_number))

    def _change_cnab_date_maturity(self, new_date, reason):
        """
        CNAB - Instrução de Alteração da Data de Vencimento.
        :param new_date: nova data de vencimento
        :param reason: descrição do motivo da alteração
        :return: deveria retornar algo ? Uma mensagem de confirmação talvez ?
        """
        # moves_to_sync = self.filtered(lambda m: m.date_maturity != new_date)
        # moves_to_sync._create_payment_order_change(new_date=new_date)

        if new_date == self.date_maturity:
            raise UserError(_(
                'New Date Maturity %s is equal to actual Date Maturity %s'
            ) % (new_date, self.date_maturity))

        # Modo de Pagto usado precisa ter o codigo de alteração do vencimento
        if not self.invoice_id.payment_mode_id.cnab_code_change_maturity_date_id:
            raise UserError(_(
                "Payment Mode %s don't has Change Date Maturity Code,"
                ' check if should have.'
            ) % self.payment_mode_id.name)

        # Checar se existe uma Instrução de CNAB ainda a ser enviada
        self._check_cnab_instruction_to_be_send()

        payorder, new_payorder = self._get_payment_order(self.invoice_id)

        self.mov_instruction_code_id = \
            self.payment_mode_id.cnab_code_change_maturity_date_id
        self.message_post(body=_(
            'Movement Instruction Code Updated for Request to'
            ' Change Maturity Date.'))
        self.create_payment_line_from_move_line(payorder)
        self.cnab_state = 'added'

        self.write({
            'date_maturity': new_date,
            'last_change_reason': reason,
        })

        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder)

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

    def _create_cnab_not_payment(self, reason):
        """
        CNAB - Não Pagamento/Inadimplencia.
        :param reason: descrição do motivo da alteração
        :return: deveria retornar algo ? Uma mensagem de confirmação talvez ?
        """
        # Modo de Pagto usado precisa ter a Conta Contabil de
        # Não Pagamento/Inadimplencia
        if not self.invoice_id.payment_mode_id.not_payment_account_id:
            raise UserError(_(
                "Payment Mode %s don't has the Account to Not Payment,"
                ' check if should have.'
            ) % self.payment_mode_id.name)

        if not self.invoice_id.payment_mode_id.cnab_write_off_code_id:
            raise UserError(_(
                "Payment Mode %s don't has the CNAB Writte Off Code,"
                ' check if should have.'
            ) % self.payment_mode_id.name)

        # Checar se existe uma Instrução de CNAB ainda a ser enviada
        self._check_cnab_instruction_to_be_send()

        payorder, new_payorder = self._get_payment_order(self.invoice_id)

        # TODO: O codigo usado seria o mesmo do writte off ?
        #  Em todos os casos?
        self.mov_instruction_code_id = \
            self.payment_mode_id.cnab_write_off_code_id
        self.message_post(body=_(
            'Movement Instruction Code Updated for Request to'
            ' Write Off, because not payment.'))
        self.create_payment_line_from_move_line(payorder)
        self.cnab_state = 'added'

        # Reconciliação e Baixa do Título
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        journal = self.payment_mode_id.fixed_journal_id
        move = move_obj.create({
            'name': 'CNAB - Banco ' + journal.bank_id.short_name + ' - Conta '
                    + journal.bank_account_id.acc_number + '- Inadimplência',
            'date': fields.Datetime.now(),
            # TODO  - Campo está sendo preenchido em outro lugar
            'ref': 'CNAB Baixa por Inadimplêcia',
            # O Campo abaixo é usado apenas para mostrar ou não a aba
            # referente ao LOG do CNAB mas nesse caso não há.
            # 'is_cnab': True,
            'journal_id': journal.id,
        })
        # Linha a ser conciliada
        counterpart_values = {
            'credit': self.amount_residual,
            'debit': 0.0,
            'account_id': self.account_id.id,
        }
        # linha referente a Conta Contabil de Inadimplecia
        move_not_payment_values = {
            'debit': self.amount_residual,
            'credit': 0.0,
            'account_id': self.invoice_id.
                payment_mode_id.not_payment_account_id.id,
        }

        commom_move_values = {
            'move_id': move.id,
            'partner_id': self.partner_id.id,
            'already_completed': True,
            'ref': self.own_number,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'company_currency_id': self.company_id.currency_id.id,
        }

        counterpart_values.update(commom_move_values)
        move_not_payment_values.update(commom_move_values)

        moves = move_line_obj.with_context(
            check_move_validity=False).create(
            (counterpart_values, move_not_payment_values)
        )

        move_line_to_reconcile = moves.filtered(
            lambda m: m.credit > 0.0)
        (self + move_line_to_reconcile).reconcile()

        self.write({
            'last_change_reason': reason,
            'payment_situation': 'nao_pagamento',
        })

        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder)

    def _create_cnab_writte_off(self):
        """
        CNAB - Instrução de Baixar de Título.
        """
        if not self.invoice_id.payment_mode_id.cnab_write_off_code_id:
            raise UserError(_(
                "Payment Mode %s don't has the CNAB Writte Off Code,"
                ' check if should have.'
            ) % self.payment_mode_id.name)

        # Checar se existe uma Instrução de CNAB ainda a ser enviada
        self._check_cnab_instruction_to_be_send()

        payorder, new_payorder = self._get_payment_order(self.invoice_id)

        self.mov_instruction_code_id = \
            self.payment_mode_id.cnab_write_off_code_id
        self.payment_situation = 'baixa_liquidacao'
        self.message_post(body=_(
            'Movement Instruction Code Updated for Request to'
            ' Write Off, because payment done in another way.'))
        self.create_payment_line_from_move_line(payorder)
        self.cnab_state = 'added_paid'

        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder)

    def _create_cnab_change_tittle_value(self):
        """
        CNAB - Alteração do Valor do Título.
        """
        if not self.payment_mode_id.cnab_code_change_title_value_id:
            raise UserError(_(
                "Payment Mode %s don't has the CNAB Change Tittle Value Code,"
                ' check if should have.'
            ) % self.payment_mode_id.name)

        # Checar se existe uma Instrução de CNAB ainda a ser enviada
        self._check_cnab_instruction_to_be_send()

        payorder, new_payorder = self._get_payment_order(self.invoice_id)

        self.mov_instruction_code_id = \
            self.payment_mode_id.cnab_code_change_title_value_id
        self.message_post(body=_(
            'Movement Instruction Code Updated for Request to'
            ' Change Title Value, because partial payment'
            ' of %d done.') % (self.debit - self.amount_residual))
        self.create_payment_line_from_move_line(payorder)

        self.cnab_state = 'added'

        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder)

    def _create_cnab_protest_tittle(self, reason):
        """
        CNAB - Protestar Título.
        """
        if not self.payment_mode_id.cnab_code_protest_title_id:
            raise UserError(_(
                "Payment Mode %s don't has the CNAB Protest Tittle Code,"
                ' check if should have.'
            ) % self.payment_mode_id.name)

        # Checar se existe uma Instrução de CNAB ainda a ser enviada
        self._check_cnab_instruction_to_be_send()

        payorder, new_payorder = self._get_payment_order(self.invoice_id)

        self.mov_instruction_code_id = \
            self.payment_mode_id.cnab_code_protest_title_id
        self.message_post(body=_(
            'Movement Instruction Code Updated for Request to Protest Title'))
        self.create_payment_line_from_move_line(payorder)

        self.cnab_state = 'added'
        self.last_change_reason = reason
        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder)

    def _create_cnab_suspend_protest_keep_wallet(self, reason):
        """
        CNAB - Sustar Protesto e Manter em Carteira.
        """
        if not self.payment_mode_id.cnab_code_suspend_protest_keep_wallet_id:
            raise UserError(_(
                "Payment Mode %s don't has the CNAB Suspend"
                " Protest and keep in Wallet Code, check if should have."
            ) % self.payment_mode_id.name)

        # Checar se existe uma Instrução de CNAB ainda a ser enviada
        self._check_cnab_instruction_to_be_send()

        payorder, new_payorder = self._get_payment_order(self.invoice_id)

        self.mov_instruction_code_id = \
            self.payment_mode_id.cnab_code_suspend_protest_keep_wallet_id
        self.message_post(body=_(
            'Movement Instruction Code Updated for Suspend'
            ' Protest and Keep in Wallet.'))
        self.create_payment_line_from_move_line(payorder)

        self.cnab_state = 'added'
        self.last_change_reason = reason
        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder)

    def _create_cnab_suspend_protest_writte_off(self, reason):
        """
        CNAB - Sustar Protesto e Baixar Titulo.
        """
        # TODO: Deveria chamar a função de Não
        #  Pagamento( _create_cnab_not_payment ) ?

        if not self.payment_mode_id.cnab_code_suspend_protest_write_off_id:
            raise UserError(_(
                "Payment Mode %s don't has the CNAB Suspend"
                " Protest and Writte Off."
            ) % self.payment_mode_id.name)

        # Checar se existe uma Instrução de CNAB ainda a ser enviada
        self._check_cnab_instruction_to_be_send()

        payorder, new_payorder = self._get_payment_order(self.invoice_id)

        self.mov_instruction_code_id = \
            self.payment_mode_id.cnab_code_suspend_protest_write_off_id
        self.message_post(body=_(
            'Movement Instruction Code Updated for Suspend'
            ' Protest and Writte Off Tittle.'))
        self.create_payment_line_from_move_line(payorder)

        self.cnab_state = 'added'
        self.last_change_reason = reason
        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder)

    def _create_change(self, change_type, new_date, reason='', **kwargs):
        if change_type == 'change_date_maturity':
            self._change_cnab_date_maturity(new_date, reason)
        elif change_type == 'change_payment_mode':
            self._change_payment_mode(reason, **kwargs)
        elif change_type == 'baixa':
            self._create_baixa(reason, **kwargs)
        elif change_type == 'not_payment':
            self._create_cnab_not_payment(reason)
        elif change_type == 'protest_tittle':
            self._create_cnab_protest_tittle(reason)
        elif change_type == 'suspend_protest_keep_wallet':
            self._create_cnab_suspend_protest_keep_wallet(reason)
        elif change_type == 'suspend_protest_writte_off':
            self._create_cnab_suspend_protest_writte_off(reason)

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
