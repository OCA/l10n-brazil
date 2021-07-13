# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants import BR_CODES_PAYMENT_ORDER, ESTADOS_CNAB, SITUACAO_PAGAMENTO


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = [_name, "l10n_br_cnab.change.methods"]
    # As linhas de cobrança precisam ser criadas conforme sequencia de
    # Data de Vencimentos/date_maturity senão ficam fora de ordem:
    #  ex.: own_number 201 31/12/2020, own_number 202 18/11/2020
    #  Isso causa confusão pois a primeira parcela fica como sendo a segunda.
    _order = "date desc, date_maturity ASC, id desc"

    cnab_state = fields.Selection(
        selection=ESTADOS_CNAB,
        string="Estados CNAB",
    )

    own_number = fields.Char(
        string="Nosso Numero",
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
        compute="_compute_own_number_without_zfill",
        store=True,
        copy=False,
    )

    # Podem existir sequencias do nosso numero/own_number iguais entre bancos
    # diferentes, porém o Diario/account.journal não pode ser o mesmo.
    journal_payment_mode_id = fields.Many2one(
        comodel_name="account.journal",
        compute="_compute_journal_payment_mode",
        store=True,
        copy=False,
    )

    document_number = fields.Char(
        string="Número documento",
    )

    company_title_identification = fields.Char(
        string="Identificação Titulo Empresa",
    )

    payment_situation = fields.Selection(
        selection=SITUACAO_PAGAMENTO,
        string="Situação do Pagamento",
        default="inicial",
    )

    instructions = fields.Text(
        string="Instruções de cobrança",
        readonly=True,
    )

    journal_entry_ref = fields.Char(
        string="Journal Entry Ref",
        compute="_compute_journal_entry_ref",
        store=True,
    )

    # TODO: Confirmar o caso de uso de diferentes modos de pagto na mesma
    #  account.invoice
    payment_mode_id = fields.Many2one(string="Modo de Pagamento")

    last_change_reason = fields.Text(
        readonly=True,
        string="Justificativa",
    )

    mov_instruction_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.mov.instruction.code",
        string="Código da Instrução para Movimento",
        help="Campo G061 do CNAB",
    )

    # Usados para deixar invisiveis/somente leitura
    # os campos relacionados ao CNAB
    payment_method_id = fields.Many2one(
        comodel_name="account.payment.method",
        related="payment_mode_id.payment_method_id",
        string="Payment Method",
    )

    payment_method_code = fields.Char(
        related="payment_method_id.code",
        readonly=True,
        store=True,
        string="Payment Method Code",
    )

    cnab_return_line_ids = fields.One2many(
        string="Retornos CNAB",
        comodel_name="l10n_br_cnab.return.event",
        readonly=True,
        inverse_name="move_line_id",
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

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        # Preenchendo apenas nos casos CNAB
        if self.payment_mode_id.payment_method_code in BR_CODES_PAYMENT_ORDER:
            vals.update(
                {
                    "own_number": self.own_number,
                    "document_number": self.document_number,
                    "company_title_identification": self.company_title_identification,
                    "payment_mode_id": self.payment_mode_id.id,
                    # Codigo de Instrução do Movimento
                    "mov_instruction_code_id": self.mov_instruction_code_id.id,
                    "communication_type": "cnab",
                    # Campos abaixo estão sendo adicionados devido ao problema de
                    # Ordens de Pagto vinculadas devido o ondelete=restrict no
                    # campo move_line_id do account.payment.line
                    # TODO: Aguardando a possibilidade de alteração no
                    #  modulo account_payment_order na v14
                    "ml_maturity_date": self.date_maturity,
                    "invoice_id": self.invoice_id.id,
                }
            )

            # Se for uma solicitação de baixa do título é preciso informar o
            # campo debit o codigo original coloca o amount_residual
            if (
                self.mov_instruction_code_id.id
                == self.payment_mode_id.cnab_write_off_code_id.id
            ):
                vals["amount_currency"] = self.credit or self.debit

            if self.env.context.get("rebate_value"):
                vals["rebate_value"] = self.env.context.get("rebate_value")

            if self.env.context.get("discount_value"):
                vals["discount_value"] = self.env.context.get("discount_value")

        return vals

    def create_payment_line_from_move_line(self, payment_order):
        """
        Altera estado do cnab para adicionado a ordem
        :param payment_order:
        :return:
        """
        for record in self:

            cnab_state = "added"
            if record.reconciled:
                cnab_state = "added_paid"

            record.cnab_state = cnab_state

        return super().create_payment_line_from_move_line(payment_order)

    def generate_boleto(self, validate=True):
        raise NotImplementedError

    def write(self, values):
        """
        Sobrescrita do método Write. Não deve ser possível voltar o cnab_state
        ou a situacao_pagamento para um estado anterior
        :param values:
        :return:
        """
        for record in self:
            cnab_state = values.get("cnab_state")

            if cnab_state and (
                record.cnab_state == "done"
                or (
                    record.cnab_state in ["accepted", "accepted_hml"]
                    and cnab_state not in ["accepted", "accepted_hml", "done"]
                )
            ):
                values.pop("cnab_state", False)

            if record.payment_situation not in ["inicial", "aberta"]:
                values.pop("payment_situation", False)

        return super().write(values)

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

    @api.depends("own_number")
    def _compute_own_number_without_zfill(self):
        """
        No arquivo de retorno do CNAB o campo pode ter um tamanho
        diferente, o tamanho do campo é preenchido na totalidade
        com zeros a esquerda, e no odoo o tamanho do sequencial pode
        estar diferente
        ex.: retorno cnab 0000000000000201 own_number 0000000201

        O campo own_number_without_zfill foi a forma que encontrei
        para poder fazer um search o nosso_numero_cnab_retorno.lstrip("0") e
        ter algo:
        ex.:
        arquivo retorno cnab 201 own_number_without_zfill 201

        É usado o lstrip() para manter os zeros a direita, exemplo:
            VALOR '0000000090'
            | strip | rstrip | lstrip | 9 000000009 90

            Valor '00000000201'
            | strip | rstrip | lstrip | 201 00000000201 201

        :return: Valor sem os zeros a esquerda
        """
        for record in self:
            if record.own_number:
                record.own_number_without_zfill = record.own_number.lstrip("0")

    @api.depends("payment_mode_id")
    def _compute_journal_payment_mode(self):
        for record in self:
            if record.payment_mode_id:
                # CNAB usa sempre a opção fixed_journal_id
                if record.payment_mode_id.fixed_journal_id:
                    record.journal_payment_mode_id = (
                        record.payment_mode_id.fixed_journal_id.id
                    )

    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):

        res = super().reconcile(writeoff_acc_id, writeoff_journal_id)
        for record in self:
            # Verificar Casos de CNAB
            if (
                record.payment_mode_id.payment_method_code in BR_CODES_PAYMENT_ORDER
                and record.payment_mode_id.payment_method_id.payment_type == "inbound"
            ):
                # Na importação do arquivo de retorno o metodo também é
                # chamado no caso do modulo l10n_br_account_payment_brcobranca
                # o contexto traz o campo 'file_name' que ao ser encontrado
                # ignora o envio de alterações CNAB, outros modulos precisam
                # validar isso
                # Caso de Não Pagamento já está criando um Pedido de Baixa
                if self.env.context.get("file_name") or self.env.context.get(
                    "not_payment"
                ):
                    continue
                if record.matched_credit_ids:
                    for line in record.matched_credit_ids:
                        if not line.already_send_cnab:
                            record.create_payment_outside_cnab(line.amount)
                            line.already_send_cnab = True

        return res


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    # Evita que uma conciliação parcial seja
    # considerada novamente em um pagamento
    already_send_cnab = fields.Boolean(string="Already send CNAB")
