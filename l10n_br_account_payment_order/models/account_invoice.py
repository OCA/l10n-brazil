#    @author Danimar Ribeiro <danimaribeiro@gmail.com>
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    SEQUENCIAL_CARTEIRA,
    SEQUENCIAL_EMPRESA,
    SEQUENCIAL_FATURA,
)

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @api.depends("state", "move_id.line_ids", "move_id.line_ids.account_id")
    def _compute_receivables(self):
        for record in self:
            lines = self.env["account.move.line"]
            for line in record.move_id.line_ids:
                if (
                    line.account_id.id == record.account_id.id
                    and line.account_id.internal_type in ("receivable", "payable")
                ):
                    lines |= line
            record.move_line_receivable_ids = lines.sorted()

    move_line_receivable_ids = fields.Many2many(
        comodel_name="account.move.line",
        string=u"Receivables",
        store=True,
        compute="_compute_receivables",
    )

    # eval_state_cnab = fields.Selection(
    #     string=u"Estado CNAB",
    #     related="move_line_receivable_id.state_cnab",
    #     readonly=True,
    #     store=True,
    #     index=True,
    # )
    #
    # eval_situacao_pagamento = fields.Selection(
    #     string=u"Situação do Pagamento",
    #     related="move_line_receivable_id.situacao_pagamento",
    #     readonly=True,
    #     store=True,
    #     index=True,
    # )

    eval_payment_mode_instrucoes = fields.Text(
        string="Instruções de Cobrança do Modo de Pagamento",
        related="payment_mode_id.instrucoes",
        readonly=True,
    )

    instrucoes = fields.Text(string="Instruções de cobrança")

    @api.onchange("payment_mode_id")
    def _onchange_payment_mode_id(self):
        tax_analytic_tag_id = self.env.ref(
            "l10n_br_account_payment_cobranca." "account_analytic_tag_tax"
        )

        to_remove_invoice_line_ids = self.invoice_line_ids.filtered(
            lambda i: tax_analytic_tag_id in i.analytic_tag_ids
        )

        self.invoice_line_ids -= to_remove_invoice_line_ids

        payment_mode_id = self.payment_mode_id
        if payment_mode_id.product_tax_id:
            invoice_line_data = {
                "name": "Taxa adicional do modo de pagamento escolhido",
                "partner_id": self.partner_id.id,
                "account_id": payment_mode_id.tax_account_id.id,
                "product_id": payment_mode_id.product_tax_id.id,
                "price_unit": payment_mode_id.product_tax_id.lst_price,
                "quantity": 1,
                "analytic_tag_ids": [(6, 0, [tax_analytic_tag_id.id])],
            }

            self.update(
                {
                    "invoice_line_ids": [
                        (6, 0, self.invoice_line_ids.ids),
                        (0, 0, invoice_line_data),
                    ]
                }
            )

    @api.onchange("payment_term_id")
    def _onchange_payment_term(self):
        interest_analytic_tag_id = self.env.ref(
            "l10n_br_account_payment_cobranca." "account_analytic_tag_interest"
        )

        to_remove_invoice_line_ids = self.invoice_line_ids.filtered(
            lambda i: interest_analytic_tag_id in i.analytic_tag_ids
        )

        self.invoice_line_ids -= to_remove_invoice_line_ids

        payment_term_id = self.payment_term_id
        amount_total = self.amount_total
        if payment_term_id.has_interest and amount_total > 0:
            invoice_line_data = {
                "name": "Taxa de juros por parcelamento no cartão",
                "partner_id": self.partner_id.id,
                "account_id": payment_term_id.interest_account_id.id,
                "analytic_tag_ids": [(6, 0, [interest_analytic_tag_id.id])],
                "quantity": 1,
                "price_unit": amount_total * payment_term_id.interest_rate / 100,
            }

            self.update(
                {
                    "invoice_line_ids": [
                        (6, 0, self.invoice_line_ids.ids),
                        (0, 0, invoice_line_data),
                    ]
                }
            )

    def _remove_payment_order_line(self, _raise=True):
        move_line_receivable_ids = self.move_line_receivable_ids
        payment_order_ids = self.env["account.payment.order"].search(
            [("payment_line_ids.move_line_id", "in", [move_line_receivable_ids.id])]
        )

        if payment_order_ids:
            draft_cancel_payment_order_ids = payment_order_ids.filtered(
                lambda p: p.state in ["draft", "cancel"]
            )
            if payment_order_ids - draft_cancel_payment_order_ids:
                if _raise:
                    raise UserError(
                        _(
                            "A fatura não pode ser cancelada pois a mesma já se "
                            "encontra exportada por uma ordem de pagamento."
                        )
                    )

            for po_id in draft_cancel_payment_order_ids:
                p_line_id = self.env["account.payment.line"].search(
                    [
                        ("order_id", "=", po_id.id),
                        ("move_line_id", "=", move_line_receivable_ids.id),
                    ]
                )
                po_id.payment_line_ids -= p_line_id

    @api.multi
    def action_invoice_cancel(self):
        for record in self:
            if record.eval_state_cnab == "accepted":
                raise UserError(
                    _(
                        "A fatura não pode ser cancelada pois já foi aprovada "
                        "no Banco."
                    )
                )
            if record.eval_state_cnab == "done":
                raise UserError(_("Não é possível cancelar uma fatura finalizada."))
            if record.eval_state_cnab == "exported":
                raise UserError(
                    _(
                        "A fatura não pode ser cancelada pois já foi exportada "
                        "em uma remessa."
                    )
                )

            record._remove_payment_order_line()

        super(AccountInvoice, self).action_invoice_cancel()

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
            # inv.transaction_id = sequence
            inv._compute_receivables()
            for index, interval in enumerate(inv.move_line_receivable_ids):
                inv_number = inv.get_invoice_fiscal_number().split("/")[-1].zfill(8)
                numero_documento = inv_number + "/" + str(index + 1).zfill(2)

                # Verificar se é boleto para criar o numero
                if inv.company_id.own_number_type == SEQUENCIAL_EMPRESA:
                    sequence = inv.company_id.get_own_number_sequence()
                elif inv.company_id.own_number_type == SEQUENCIAL_FATURA:
                    sequence = numero_documento.replace("/", "")
                elif inv.company_id.own_number_type == SEQUENCIAL_CARTEIRA:
                    if not inv.payment_mode_id.own_number_sequence:
                        raise UserError(
                            _(
                                "Favor acessar aba Cobrança da configuração"
                                " do Modo de Pagamento e determinar o "
                                "campo Sequência do Nosso Número."
                            )
                        )
                    sequence = inv.payment_mode_id.get_own_number_sequence()
                else:
                    raise UserError(
                        _(
                            "Favor acessar aba Cobrança da configuração da"
                            " sua empresa para determinar o tipo de "
                            "sequencia utilizada nas cobrancas"
                        )
                    )

                interval.transaction_ref = sequence
                interval.nosso_numero = (
                    sequence if interval.payment_mode_id.gera_nosso_numero else "0"
                )
                interval.numero_documento = numero_documento
                interval.identificacao_titulo_empresa = hex(interval.id).upper()
                instrucoes = ""
                if inv.eval_payment_mode_instrucoes:
                    instrucoes = inv.eval_payment_mode_instrucoes + "\n"
                if inv.instrucoes:
                    instrucoes += inv.instrucoes + "\n"
                interval.instrucoes = instrucoes

    @api.multi
    def action_move_create(self):
        result = super(AccountInvoice, self).action_move_create()

        self._pos_action_move_create()
        return result

    @api.multi
    def create_account_payment_line_baixa(self):

        for inv in self:

            applicable_lines = inv.move_id.line_ids.filtered(
                lambda x: (
                    x.payment_mode_id.payment_order_ok
                    and x.account_id.internal_type in ("receivable", "payable")
                )
            )

            if not applicable_lines:
                raise UserError(
                    _(
                        "No Payment Line created for invoice %s because "
                        "it's internal type isn't receivable or payable."
                    )
                    % inv.number
                )

            payment_modes = applicable_lines.mapped("payment_mode_id")
            if not payment_modes:
                raise UserError(_("No Payment Mode on invoice %s") % inv.number)

            result_payorder_ids = []
            apoo = self.env["account.payment.order"]
            for payment_mode in payment_modes:
                payorder = apoo.search(
                    [
                        ("payment_mode_id", "=", payment_mode.id),
                        ("state", "=", "draft"),
                    ],
                    limit=1,
                )

                new_payorder = False
                if not payorder:
                    payorder = apoo.create(
                        inv._prepare_new_payment_order(payment_mode)
                    )
                    new_payorder = True
                result_payorder_ids.append(payorder.id)
                count = 0
                for line in applicable_lines.filtered(
                    lambda x: x.payment_mode_id == payment_mode
                ):
                    line.create_payment_line_from_move_line(payorder)
                    count += 1
                if new_payorder:
                    inv.message_post(
                        body=_(
                            "%d payment lines added to the new draft payment "
                            "order %s which has been automatically created."
                        )
                        % (count, payorder.name)
                    )
                else:
                    inv.message_post(
                        body=_(
                            "%d payment lines added to the existing draft "
                            "payment order %s."
                        )
                        % (count, payorder.name)
                    )

    @api.multi
    def invoice_validate(self):
        result = super(AccountInvoice, self).invoice_validate()
        filtered_invoice_ids = self.filtered(lambda s: s.payment_mode_id)
        if filtered_invoice_ids:
            filtered_invoice_ids.create_account_payment_line()
        return result

    @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        self.ensure_one()

        if self.payment_term_id.payment_mode_selection == "cartao":
            raise UserError(
                _(
                    "Não é possível adicionar pagamentos em uma fatura "
                    "parcelada no cartão de crédito"
                )
            )
        if self.eval_situacao_pagamento in ["paga", "liquidada", "baixa_liquidacao"]:
            raise UserError(
                _(
                    "Não é possível adicionar pagamentos em uma fatura que "
                    "já está paga."
                )
            )
        if self.eval_state_cnab in ["accepted", "exported", "done"]:
            raise UserError(
                _(
                    "Não é possível adicionar pagamentos em uma fatura já "
                    "exportada ou aceita no banco."
                )
            )
        return super(AccountInvoice, self).assign_outstanding_credit(credit_aml_id)

    @api.multi
    def register_payment(
        self, payment_line, writeoff_acc_id=False, writeoff_journal_id=False
    ):
        res = super(AccountInvoice, self).register_payment(
            payment_line, writeoff_acc_id, writeoff_journal_id
        )

        self._pos_action_move_create()

        for inv in self:
            inv._compute_receivables()
            receivable_id = inv.move_line_receivable_ids
            receivable_id.residual = inv.residual

        return res
