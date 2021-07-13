# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class L10nBrCNABChangeMethods(models.Model):
    _name = "l10n_br_cnab.change.methods"
    _description = "Methods used to make changes in CNAB Movement."

    def _identify_cnab_change(
        self, change_type, new_date, rebate_value, discount_value, reason="", **kwargs
    ):
        """
        CNAB - Alterações possíveis
        :param change_type:
        :param new_date: Nova Data de Vencimento
        :param rebate_value: Valor do Abatimento
        :param discount_value: Valor do Desconto
        :param reason: Justificatica de alteração
        :param kwargs:
        :return:
        """
        for record in self:
            # Checar se existe uma Instrução de CNAB ainda a ser enviada
            record._check_cnab_instruction_to_be_send()

            payorder, new_payorder = record._get_payment_order(record.invoice_id)

            if change_type == "change_date_maturity":
                cnab_code = record._get_cnab_date_maturity(new_date)
                record._make_cnab_change(cnab_code, new_payorder, payorder, reason)
            elif change_type == "change_payment_mode":
                record._change_payment_mode(reason, **kwargs)
            elif change_type == "baixa":
                record._create_baixa(reason, **kwargs)
            elif change_type == "not_payment":
                record._create_cnab_not_payment(payorder, new_payorder, reason)
            elif change_type == "protest_tittle":
                cnab_code = record._get_cnab_protest_tittle()
                record._make_cnab_change(cnab_code, new_payorder, payorder, reason)
            elif change_type == "suspend_protest_keep_wallet":
                cnab_code = record._get_cnab_suspend_protest_keep_wallet()
                record._make_cnab_change(cnab_code, new_payorder, payorder, reason)
            elif change_type == "suspend_protest_writte_off":
                cnab_code = record._get_cnab_suspend_protest_writte_off()
                record._make_cnab_change(cnab_code, new_payorder, payorder, reason)
            elif change_type == "grant_rebate":
                cnab_code = record._get_cnab_grant_rebate()
                record.with_context(rebate_value=rebate_value)._make_cnab_change(
                    cnab_code, new_payorder, payorder, reason
                )
            elif change_type == "cancel_rebate":
                cnab_code = record._get_cnab_cancel_rebate()
                record._make_cnab_change(cnab_code, new_payorder, payorder, reason)
            elif change_type == "grant_discount":
                cnab_code = record._get_cnab_grant_discount()
                record.with_context(discount_value=discount_value)._make_cnab_change(
                    cnab_code, new_payorder, payorder, reason
                )
            elif change_type == "cancel_discount":
                cnab_code = record._get_cnab_cancel_discount()
                record._make_cnab_change(cnab_code, new_payorder, payorder, reason)

    def _get_payment_order(self, invoice):
        """
        CNAB - Obtem a Ordem de Pagamento a ser usada e se é uma nova
        :param invoice:
        :return: Orderm de Pagamento, E se é uma nova
        """

        # Verificar Ordem de Pagto
        apo = self.env["account.payment.order"]
        # Existe a possibilidade de uma Fatura ter diferentes
        # Modos de Pagto nas linhas no caso CNAB ?
        payorder = apo.search(
            [
                ("payment_mode_id", "=", invoice.payment_mode_id.id),
                ("state", "=", "draft"),
            ],
            limit=1,
        )
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
            lambda t: t.order_id.state in ("draft", "open", "generated")
        )
        if payment_line_to_be_send:
            raise UserError(
                _(
                    "There is a CNAB Payment Order %s in status %s"
                    " related to invoice %s created, the CNAB file"
                    " should be sent to bank, because only after"
                    " that it is possible make another CNAB Instruction."
                )
                % (
                    payment_line_to_be_send.order_id.name,
                    payment_line_to_be_send.order_id.state,
                    self.invoice_id.number,
                )
            )

    def _msg_cnab_payment_order_at_invoice(self, new_payorder, payorder, reason):
        """
        CNAB - Registra a mensagem de alteração na Fatura para rastreabilidade.
        :param new_payorder: Se é uma nova Ordem de Pagamento/Debito
        :param payorder: Objeto Ordem de Pagamento/Debito
        :return:
        """

        cnab_instruction = (
            self.mov_instruction_code_id.code
            + " - "
            + self.mov_instruction_code_id.name
        )
        if new_payorder:
            self.invoice_id.message_post(
                body=_(
                    "Payment line added to the the new draft payment "
                    "order %s which has been automatically created,"
                    " to send CNAB Instruction %s for OWN NUMBER %s.\n"
                    "Justification: %s"
                )
                % (payorder.name, cnab_instruction, self.own_number, reason)
            )
        else:
            self.invoice_id.message_post(
                body=_(
                    "Payment line added to the existing draft "
                    "order %s to send CNAB Instruction %s for OWN NUMBER %s.\n"
                    "Justification: %s"
                )
                % (payorder.name, cnab_instruction, self.own_number, reason)
            )

    def _msg_error_cnab_missing(self, payment_mode_name, missing):
        """
        CNAB - Não é possível fazer a alteração pois falta algo
        :param payment_mode_name: Nome do Modo de Pagamento
        :param missing: descrição do que falta
        :return: Mensagem de Erro
        """
        raise UserError(
            _(
                "Payment Mode %s don't has %s for making CNAB change,"
                " check if should have."
            )
            % (payment_mode_name, missing)
        )

    def _cnab_already_start(self):

        result = False
        # Se existir uma Ordem já gerada, exportada ou concluída
        # significa que o processo desse CNAB já foi iniciado no Banco
        cnab_already_start = self.payment_line_ids.filtered(
            lambda t: t.order_id.state in ("generated", "uploaded", "done")
        )

        if cnab_already_start:
            result = True

        return result

    def update_cnab_for_cancel_invoice(self):

        cnab_already_start = self._cnab_already_start()
        if cnab_already_start:
            reason_write_off = (
                "Movement Instruction Code Updated for Request to Write Off,"
                " because Invoice %s was Cancel."
            ) % self.invoice_id.name
            payment_situation = "fatura_cancelada"
            self.create_cnab_write_off(reason_write_off, payment_situation)
        else:
            # Processo de CNAB ainda não iniciado a linha será apenas excluida
            self.payment_line_ids.unlink()

    def _get_cnab_date_maturity(self, new_date):
        """
        CNAB - Instrução de Alteração da Data de Vencimento.
        :param new_date: nova data de vencimento
        :param reason: descrição do motivo da alteração
        :return: deveria retornar algo ? Uma mensagem de confirmação talvez ?
        """

        if new_date == self.date_maturity:
            raise UserError(
                _("New Date Maturity %s is equal to actual Date Maturity %s")
                % (new_date, self.date_maturity)
            )

        # Modo de Pagto usado precisa ter o codigo de alteração do vencimento
        if not self.invoice_id.payment_mode_id.cnab_code_change_maturity_date_id:
            self._msg_error_cnab_missing(
                self.payment_mode_id.name, "Date Maturity Code"
            )

        self.date_maturity = new_date

        return self.payment_mode_id.cnab_code_change_maturity_date_id

    def _create_cnab_not_payment(self, payorder, new_payorder, reason):
        """
        CNAB - Não Pagamento/Inadimplencia.
        :param reason: descrição do motivo da alteração
        :return: deveria retornar algo ? Uma mensagem de confirmação talvez ?
        """
        # Modo de Pagto usado precisa ter a Conta Contabil de
        # Não Pagamento/Inadimplencia
        if not self.invoice_id.payment_mode_id.not_payment_account_id:
            self._msg_error_cnab_missing(
                self.payment_mode_id.name, "the Account to Not Payment"
            )

        if not self.invoice_id.payment_mode_id.cnab_write_off_code_id:
            self._msg_error_cnab_missing(self.payment_mode_id.name, "Writte Off Code")

        # TODO: O codigo usado seria o mesmo do writte off ?
        #  Em todos os casos?
        self.mov_instruction_code_id = self.payment_mode_id.cnab_write_off_code_id

        # Reconciliação e Baixa do Título
        move_obj = self.env["account.move"]
        move_line_obj = self.env["account.move.line"]
        journal = self.payment_mode_id.fixed_journal_id
        move = move_obj.create(
            {
                "name": "CNAB - Banco "
                + journal.bank_id.short_name
                + " - Conta "
                + journal.bank_account_id.acc_number
                + "- Inadimplência",
                "date": fields.Datetime.now(),
                # TODO  - Campo está sendo preenchido em outro lugar
                "ref": "CNAB Baixa por Inadimplêcia",
                # O Campo abaixo é usado apenas para mostrar ou não a aba
                # referente ao LOG do CNAB mas nesse caso não há.
                # 'is_cnab': True,
                "journal_id": journal.id,
            }
        )
        # Linha a ser conciliada
        counterpart_values = {
            "credit": self.amount_residual,
            "debit": 0.0,
            "account_id": self.account_id.id,
        }
        # linha referente a Conta Contabil de Inadimplecia
        move_not_payment_values = {
            "debit": self.amount_residual,
            "credit": 0.0,
            "account_id": self.invoice_id.payment_mode_id.not_payment_account_id.id,
        }

        commom_move_values = {
            "move_id": move.id,
            "partner_id": self.partner_id.id,
            "already_completed": True,
            "ref": self.own_number,
            "journal_id": journal.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "company_currency_id": self.company_id.currency_id.id,
        }

        counterpart_values.update(commom_move_values)
        move_not_payment_values.update(commom_move_values)

        moves = move_line_obj.with_context(check_move_validity=False).create(
            (counterpart_values, move_not_payment_values)
        )

        move_line_to_reconcile = moves.filtered(lambda m: m.credit > 0.0)
        (self + move_line_to_reconcile).with_context(not_payment=True).reconcile()

        self.create_payment_line_from_move_line(payorder)
        # Proceso CNAB encerrado
        self.cnab_state = "done"
        self.payment_situation = "nao_pagamento"

        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder, reason)

    def remove_payment_line(self, reason, payment_situation):
        """
        Remove a Linha de Pagamento
        :param reason:
        :param payment_situation:
        :return:
        """
        self.payment_line_ids.unlink()
        # Ordem de Pagto ainda não confirmada
        # será apagada a linha
        self.payment_situation = payment_situation
        # TODO criar um state removed ?
        self.cnab_state = "done"
        self.invoice_id.message_post(body=_(reason))

    def create_cnab_write_off(self, reason, payment_situation):
        """
        CNAB - Instrução de Baixar de Título.
        """

        # Caso a Ordem ainda em Draft as linhas serão somente apagadas
        cnab_already_start = self._cnab_already_start()
        payment_lines_removed = False
        if not cnab_already_start:
            # So tem uma linha nesse caso
            if self.payment_line_ids[0].order_id.state == "draft":
                reason = (
                    "Removed Payline that would be sent to Bank"
                    " by CNAB because amount payment was made"
                    " before sending."
                )
                payment_situation = "baixa_liquidacao"
                self.remove_payment_line(reason, payment_situation)
                payment_lines_removed = True

        if not self.invoice_id.payment_mode_id.cnab_write_off_code_id:
            self._msg_error_cnab_missing(self.payment_mode_id.name, "Write Off Code")

        if not payment_lines_removed:
            # Checar se existe uma Instrução de CNAB ainda a ser enviada
            self._check_cnab_instruction_to_be_send()

            payorder, new_payorder = self._get_payment_order(self.invoice_id)

            self.mov_instruction_code_id = self.payment_mode_id.cnab_write_off_code_id
            self.payment_situation = payment_situation

            self.create_payment_line_from_move_line(payorder)
            self.cnab_state = "added_paid"

            # Registra as Alterações na Fatura
            self._msg_cnab_payment_order_at_invoice(new_payorder, payorder, reason)

    def create_cnab_change_tittle_value(self):
        """
        CNAB - Alteração do Valor do Título.
        """
        if not self.payment_mode_id.cnab_code_change_title_value_id:
            self._msg_error_cnab_missing(self.payment_mode_id.name, "Tittle Value Code")

        # Checar se existe uma Instrução de CNAB ainda a ser enviada
        self._check_cnab_instruction_to_be_send()

        payorder, new_payorder = self._get_payment_order(self.invoice_id)

        self.mov_instruction_code_id = (
            self.payment_mode_id.cnab_code_change_title_value_id
        )
        reason = (
            "Movement Instruction Code Updated for Request to "
            "Change Title Value, because partial payment "
            "of %d done."
        ) % (self.debit - self.amount_residual)

        self.create_payment_line_from_move_line(payorder)

        self.cnab_state = "added"

        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder, reason)

    def _get_cnab_protest_tittle(self):
        """
        CNAB - Protestar Título.
        """
        if not self.payment_mode_id.cnab_code_protest_title_id:
            self._msg_error_cnab_missing(
                self.payment_mode_id.name, "Protest Tittle Code"
            )

        return self.payment_mode_id.cnab_code_protest_title_id

    def _get_cnab_suspend_protest_keep_wallet(self):
        """
        CNAB - Sustar Protesto e Manter em Carteira.
        """
        if not self.payment_mode_id.cnab_code_suspend_protest_keep_wallet_id:
            self._msg_error_cnab_missing(
                self.payment_mode_id.name, "Suspend Protest and Keep in Wallet Code"
            )

        return self.payment_mode_id.cnab_code_suspend_protest_keep_wallet_id

    def _get_cnab_suspend_protest_writte_off(self):
        """
        CNAB - Sustar Protesto e Baixar Titulo.
        """
        # TODO: Deveria chamar a função de Não
        #  Pagamento( _create_cnab_not_payment ) ?

        if not self.payment_mode_id.cnab_code_suspend_protest_write_off_id:
            self._msg_error_cnab_missing(
                self.payment_mode_id.name, "Suspend Protest and Writte Off Code"
            )

        return self.payment_mode_id.cnab_code_suspend_protest_write_off_id

    def _get_cnab_grant_rebate(self):
        """
        CNAB - Conceder Abatimento.
        :param rebate_value: Valor do Abatimento
        :param reason: Descrição sobre alteração
        """
        if not self.payment_mode_id.cnab_code_grant_rebate_id:
            self._msg_error_cnab_missing(self.payment_mode_id.name, "Grant Rebate Code")

        return self.payment_mode_id.cnab_code_grant_rebate_id

    def _get_cnab_cancel_rebate(self):
        """
        CNAB - Cancelar Abatimento.
        :param reason: Descrição sobre alteração
        """
        if not self.payment_mode_id.cnab_code_cancel_rebate_id:
            self._msg_error_cnab_missing(
                self.payment_mode_id.name, "Cancel Rebate Code"
            )

        return self.payment_mode_id.cnab_code_cancel_rebate_id

    def _get_cnab_grant_discount(self):
        """
        CNAB - Conceder Desconto.
        :param discount_value: Valor do Desconto
        :param reason: Descrição sobre alteração
        """
        if not self.payment_mode_id.cnab_code_grant_discount_id:
            self._msg_error_cnab_missing(
                self.payment_mode_id.name, "Grant Discount Code"
            )

        return self.payment_mode_id.cnab_code_grant_discount_id

    def _get_cnab_cancel_discount(self):
        """
        CNAB - Cancelar Desconto.
        :param reason: Descrição sobre alteração
        """
        if not self.payment_mode_id.cnab_code_cancel_discount_id:
            self._msg_error_cnab_missing(
                self.payment_mode_id.name, "Cancel Discount Code"
            )

        return self.payment_mode_id.cnab_code_cancel_discount_id

    def _make_cnab_change(self, cnab_code, new_payorder, payorder, reason):
        """
        CNAB - Realiza a Alteração Generica
        :param cnab_code: Codigo CNAB a ser usado
        :param new_payorder: se é uma nova Ordem de Pagto
        :param payorder: objeto da Ordem de Pagto
        :param reason: justificativa
        :return:
        """

        rebate_value = discount_value = False
        if self.env.context.get("rebate_value"):
            rebate_value = self.env.context.get("rebate_value")

        if self.env.context.get("discount_value"):
            discount_value = self.env.context.get("discount_value")

        self.mov_instruction_code_id = cnab_code
        self.with_context(
            rebate_value=rebate_value, discount_value=discount_value
        ).create_payment_line_from_move_line(payorder)

        self.cnab_state = "added"
        # Registra as Alterações na Fatura
        self._msg_cnab_payment_order_at_invoice(new_payorder, payorder, reason)

    def _create_payment_order_change(self, **kwargs):
        self.ensure_one()
        # TODO:
        raise NotImplementedError

    def _change_payment_mode(self, reason, new_payment_mode_id, **kwargs):
        moves_to_sync = self.filtered(
            lambda m: m.payment_mode_id != new_payment_mode_id
        )
        moves_to_sync._create_payment_order_change(
            new_payment_mode_id=new_payment_mode_id, **kwargs
        )
        moves_to_sync.write(
            {
                "payment_mode_id": new_payment_mode_id.id,
                "last_change_reason": reason,
            }
        )

    def _create_baixa(self, reason, **kwargs):
        moves_to_sync = self.filtered(lambda m: True)
        # TODO: Verificar restrições possíveis
        moves_to_sync._create_payment_order_change(baixa=True, **kwargs)
        moves_to_sync.write(
            {
                "last_change_reason": reason,
                "payment_situation": "baixa",  # FIXME: Podem ser múltiplos motivos
            }
        )

    def create_payment_outside_cnab(self, amount_payment):

        if self.amount_residual == 0.0:
            reason_write_off = (
                "Movement Instruction Code Updated for"
                " Request to Write Off, because payment"
                " of %s done outside CNAB."
            ) % amount_payment
            payment_situation = "baixa_liquidacao"
            self.create_cnab_write_off(reason_write_off, payment_situation)
        else:
            self.create_cnab_change_tittle_value()
