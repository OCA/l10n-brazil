#    @author Danimar Ribeiro <danimaribeiro@gmail.com>
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants import BR_CODES_PAYMENT_ORDER


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.depends("move_id.line_ids", "move_id.state")
    def _compute_financial(self):
        for invoice in self:
            lines = invoice.move_id.line_ids.filtered(
                lambda l: l.account_id == invoice.account_id
                and l.account_id.internal_type in ("receivable", "payable")
            )
            invoice.financial_move_line_ids = lines.sorted()

    eval_payment_mode_instructions = fields.Text(
        string="Instruções de Cobrança do Modo de Pagamento",
        related="payment_mode_id.instructions",
        readonly=True,
        help="Instruções Ordem de Pagamento configuradas" " no Modo de pagamento",
    )

    instructions = fields.Text(
        string="Instruções de cobrança", help="Instruções Extras da Ordem de Pagamento"
    )

    # eval_situacao_pagamento = fields.Selection(
    #     string=u'Situação do Pagamento',
    #     related='move_line_receivable_id.situacao_pagamento',
    #     readonly=True,
    #     store=True,
    #     index=True,
    # )

    # TODO: Campo duplicado em l10n_br_account, para não ter dependencia direta
    #  do modulo, aguardando separação l10n_br_account e l10n_br_account_fiscal
    financial_move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        string="Financial Move Lines",
        store=True,
        compute="_compute_financial",
    )

    @api.onchange("payment_mode_id")
    def _onchange_payment_mode_id(self):
        tax_analytic_tag_id = self.env.ref(
            "l10n_br_account_payment_order.account_analytic_tag_tax"
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
                "account_id": payment_mode_id.product_tax_account_id.id,
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

    def action_invoice_cancel(self):
        for record in self:
            if record.payment_mode_id.payment_method_code in BR_CODES_PAYMENT_ORDER:
                for line in record.move_id.line_ids:
                    # Verificar a situação do CNAB para apenas apagar
                    # a linha ou mandar uma solicitação de Baixa
                    line.update_cnab_for_cancel_invoice()

        return super().action_invoice_cancel()

    def get_invoice_fiscal_number(self):
        """Como neste modulo nao temos o numero do documento fiscal,
        vamos retornar o numero do core e deixar este metodo
        para caso alguem queira sobrescrever"""
        self.ensure_one()
        return self.number

    def _pos_action_move_create(self):
        for inv in self:
            # Se não possui Modo de Pagto não há nada a ser feito
            if not inv.payment_mode_id:
                continue
            # Se não gera Ordem de Pagto não há nada a ser feito
            if not inv.payment_mode_id.payment_order_ok:
                continue
            # Podem existir Modo de Pagto q geram Ordens mas não são CNAB
            # por isso nesse caso tbm nada a ser feito
            if inv.payment_mode_id.payment_method_code not in BR_CODES_PAYMENT_ORDER:
                continue

            # TODO - apesar do campo financial_move_line_ids ser do tipo
            #  compute esta sendo preciso chamar o metodo porque as vezes
            #  ocorre da linha vir vazia o que impede de entrar no FOR
            #  abaixo causando o não preenchimento de dados usados no Boleto,
            #  isso deve ser melhor investigado
            inv._compute_financial()

            for index, interval in enumerate(inv.financial_move_line_ids):
                inv_number = inv.get_invoice_fiscal_number().split("/")[-1].zfill(8)
                numero_documento = inv_number + "/" + str(index + 1).zfill(2)

                sequence = inv.payment_mode_id.get_own_number_sequence(
                    inv, numero_documento
                )

                interval.transaction_ref = sequence
                interval.own_number = (
                    sequence if interval.payment_mode_id.generate_own_number else "0"
                )
                interval.document_number = numero_documento
                interval.company_title_identification = hex(interval.id).upper()
                instructions = ""
                if inv.eval_payment_mode_instructions:
                    instructions = inv.eval_payment_mode_instructions + "\n"
                if inv.instructions:
                    instructions += inv.instructions + "\n"
                interval.instructions = instructions
                # Codigo de Instrução do Movimento pode variar,
                # mesmo no CNAB 240
                interval.mov_instruction_code_id = (
                    inv.payment_mode_id.cnab_sending_code_id.id
                )

    def action_move_create(self):
        result = super().action_move_create()
        self._pos_action_move_create()
        return result

    def invoice_validate(self):
        result = super().invoice_validate()
        filtered_invoice_ids = self.filtered(
            lambda s: (
                s.payment_mode_id and s.payment_mode_id.auto_create_payment_order
            )
        )
        if filtered_invoice_ids:
            filtered_invoice_ids.create_account_payment_line()
        return result
