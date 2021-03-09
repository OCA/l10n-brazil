#    @author Danimar Ribeiro <danimaribeiro@gmail.com>
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    eval_payment_mode_instructions = fields.Text(
        string='Instruções de Cobrança do Modo de Pagamento',
        related='payment_mode_id.instructions',
        readonly=True,
    )

    instructions = fields.Text(
        string='Instruções de cobrança',
    )

    # eval_situacao_pagamento = fields.Selection(
    #     string=u'Situação do Pagamento',
    #     related='move_line_receivable_id.situacao_pagamento',
    #     readonly=True,
    #     store=True,
    #     index=True,
    # )

    @api.onchange('payment_mode_id')
    def _onchange_payment_mode_id(self):
        tax_analytic_tag_id = self.env.ref(
            'l10n_br_account_payment_order.account_analytic_tag_tax')

        to_remove_invoice_line_ids = self.invoice_line_ids.filtered(
            lambda i: tax_analytic_tag_id in i.analytic_tag_ids
        )

        self.invoice_line_ids -= to_remove_invoice_line_ids

        payment_mode_id = self.payment_mode_id
        if payment_mode_id.product_tax_id:
            invoice_line_data = {
                'name': 'Taxa adicional do modo de pagamento escolhido',
                'partner_id': self.partner_id.id,
                'account_id': payment_mode_id.product_tax_account_id.id,
                'product_id': payment_mode_id.product_tax_id.id,
                'price_unit': payment_mode_id.product_tax_id.lst_price,
                'quantity': 1,
                'analytic_tag_ids': [(6, 0, [tax_analytic_tag_id.id])],
            }

            self.update(
                {
                    'invoice_line_ids': [
                        (6, 0, self.invoice_line_ids.ids),
                        (0, 0, invoice_line_data),
                    ]
                }
            )

    @api.multi
    def action_invoice_cancel(self):
        for record in self:
            if record.payment_mode_id.payment_method_code in \
                    ('240', '400', '500'):
                for line in record.move_id.line_ids:
                    # Verificar a situação do CNAB para apenas apagar
                    # a linha ou mandar uma solicitação de Baixa
                    line.update_cnab_for_cancel_invoice()

        return super().action_invoice_cancel()

    @api.multi
    def get_invoice_fiscal_number(self):
        """ Como neste modulo nao temos o numero do documento fiscal,
        vamos retornar o numero do core e deixar este metodo
        para caso alguem queira sobrescrever"""
        self.ensure_one()
        return self.number

    @api.multi
    def _pos_action_move_create(self):
        for inv in self:
            # TODO - apesar do campo financial_move_line_ids ser do tipo
            #  compute esta sendo preciso chamar o metodo porque as vezes
            #  ocorre da linha vir vazia o que impede de entrar no FOR
            #  abaixo causando o não preenchimento de dados usados no Boleto,
            #  isso deve ser melhor investigado
            if not inv.payment_mode_id:
                continue
            inv._compute_financial()

            # Verifica se gera Ordem de Pagamento
            if not inv.payment_mode_id.payment_order_ok:
                continue

            for index, interval in enumerate(inv.financial_move_line_ids):
                inv_number = inv.get_invoice_fiscal_number().split('/')[-1].zfill(8)
                numero_documento = inv_number + '/' + str(index + 1).zfill(2)

                sequence = inv.payment_mode_id.get_own_number_sequence(
                    inv, numero_documento)

                interval.transaction_ref = sequence
                interval.own_number = (
                    sequence if interval.payment_mode_id.generate_own_number
                    else '0'
                )
                interval.document_number = numero_documento
                interval.company_title_identification = hex(interval.id).upper()
                instructions = ''
                if inv.eval_payment_mode_instructions:
                    instructions = inv.eval_payment_mode_instructions + '\n'
                if inv.instructions:
                    instructions += inv.instructions + '\n'
                interval.instructions = instructions
                # Codigo de Instrução do Movimento pode variar,
                # mesmo no CNAB 240
                interval.mov_instruction_code_id = \
                    inv.payment_mode_id.cnab_sending_code_id.id

    @api.multi
    def action_move_create(self):
        result = super().action_move_create()
        self._pos_action_move_create()
        return result

    @api.multi
    def create_payment_outside_cnab(self, amount_payment):
        """
        Em caso de CNAB é preciso verificar e criar linha(s)
         com Codigo de Instrução do Movimento de Baixa
         ou de Alteração de Valor do Título quando existir.
        :param amount_payment: Valor Pago
        :return:
        """

        # Identificar a Linha CNAB que vai ser dado Baixa ou
        # terá o Valor do Titulo alterado devido a um pagamento parcial
        applicable_lines = change_tittle_value_line = \
            self.env['account.move.line']

        lines_to_check = self.move_id.line_ids.filtered(
            lambda x: x.debit > 0.0 and x.payment_situation in ('inicial', 'aberta')
        )

        # Valor Total, baixar todas as Parcelas em Aberto
        if self.amount_total == amount_payment:
            applicable_lines |= lines_to_check
        else:
            # Verificar se é o pagto de mais de uma parcela
            # OBS.: A sequencia/order da alocação de valores e baixas/alteração
            # de valor segue as Datas de Vencimento, porque não pode ser pago
            # fora dessa ordem.
            amount_value = 0.0
            for line in lines_to_check:
                applicable_lines |= line
                amount_value += line.debit
                if amount_value == amount_payment:
                    # Valor Pago corresponde as linhas já percorridas
                    break
                if amount_value > amount_payment:
                    # Valor Pago ficou menor que as linhas de debito essa linha
                    # foi paga parcialmente e essa Parcela deverá ter seu valor
                    # alterado
                    change_tittle_value_line = line
                    break

        reason_write_off = (
            ('Movement Instruction Code Updated for Request'
             ' to Write Off, because payment of %s done outside CNAB.')
            % amount_payment)
        payment_situation = 'baixa_liquidacao'
        for line in applicable_lines:
            if line == change_tittle_value_line:
                line.create_cnab_change_tittle_value()
            else:
                line.create_cnab_write_off(reason_write_off, payment_situation)

    @api.multi
    def invoice_validate(self):
        result = super().invoice_validate()
        filtered_invoice_ids = self.filtered(lambda s: s.payment_mode_id)
        if filtered_invoice_ids:
            for filtered_invoice_id in filtered_invoice_ids:
                # Criando Ordem de Pagto Automaticamente
                if filtered_invoice_id.payment_mode_id.payment_order_ok:
                    filtered_invoice_id.create_account_payment_line()
        return result

    @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        self.ensure_one()
        # TODO - Existe necessidade de ser feito algo nesse metodo ?
        #  O Metodo parece ser chamado apenas no modulo sale
        #  https://github.com/OCA/OCB/blob/12.0/addons/sale/
        #  models/account_invoice.py#L68
        # if self.eval_situacao_pagamento in ['paga', 'liquidada',
        # 'baixa_liquidacao']:
        #    raise UserError(
        #       _(
        #         'Não é possível adicionar pagamentos em uma fatura que '
        #         'já está paga.'
        #         )
        #        )
        # if self.eval_state_cnab in ['accepted', 'exported', 'done']:
        #    raise UserError(
        #      _(
        #        'Não é possível adicionar pagamentos em uma fatura já '
        #        'exportada ou aceita no banco.'
        #        )
        #     )
        return super().assign_outstanding_credit(credit_aml_id)

    @api.multi
    def register_payment(
        self, payment_line, writeoff_acc_id=False, writeoff_journal_id=False
    ):
        res = super().register_payment(
            payment_line, writeoff_acc_id, writeoff_journal_id)

        self._pos_action_move_create()

        for inv in self:
            inv._compute_financial()
            receivable_id = inv.financial_move_line_ids
            receivable_id.residual = inv.residual

        return res

    @api.multi
    def action_cancel(self):
        # TODO: Não está chamando o super, devido problema mais abaixo,
        #  verificar se é possível
        moves = self.env['account.move']
        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            # unreconcile all journal items of the invoice, since the
            # cancellation will unlink them anyway
            inv.move_id.line_ids.filtered(
                lambda x: x.account_id.reconcile).remove_move_reconcile()

        # First, set the invoices as cancelled and detach the move ids
        self.write({'state': 'cancel', 'move_id': False})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too

            # TODO: No caso de Ordens de Pagto vinculadas devido o
            #  ondelet=restrict no campo move_line_id do account.payment.line
            #  não é possível Cancelar uma Invoice que já tenha uma Ordem de
            #  Pagto confirmada, acontece erro devido o unlink abaixo, a forma
            #  encontrada até agora é não apagar as que forem referentes a um
            #  CNAB. Verificar se o mesmo problema acontece no uso
            #  internacional e se na migração isso pode ser resolvido
            #  de uma melhor forma.
            if self.payment_mode_id.payment_method_code not in \
                    ('240', '400', '500'):
                moves.unlink()
        return True
