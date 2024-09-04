# © 2019 KMEE INFORMATICA LTDA
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants import BR_CODES_PAYMENT_ORDER


class AccountMove(models.Model):
    _inherit = "account.move"

    cnab_return_log_id = fields.Many2one(
        string="CNAB Return Log",
        comodel_name="l10n_br_cnab.return.log",
        readonly=True,
    )

    # Usado para deixar invisivel o campo
    # relacionado ao CNAB na visao
    is_cnab = fields.Boolean(string="Is CNAB?")

    eval_payment_mode_instructions = fields.Text(
        string="Instruções de Cobrança do Modo de Pagamento",
        related="payment_mode_id.instructions",
        readonly=True,
        help="Instruções Ordem de Pagamento configuradas" " no Modo de pagamento",
    )

    instructions = fields.Text(
        string="Instruções de cobrança", help="Instruções Extras da Ordem de Pagamento"
    )

    file_boleto_pdf_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Boleto PDF",
        ondelete="restrict",
        copy=False,
    )

    # Usado para deixar invisivel o botão
    # Imprimir Boleto, quando não for o caso
    payment_method_code = fields.Char(related="payment_mode_id.payment_method_id.code")

    def generate_boleto_pdf(self):
        """
        Classe a ser herdada pelo modulo que implementa a biblioteca
        ou API, deve anexar o PDF com boletos
        """
        # Veja exemplo em:
        # l10n_br_account_payment_brcobranca/models/account_move.py
        return None

    def _target_new_tab(self, attachment_id):
        if attachment_id:
            return {
                "type": "ir.actions.act_url",
                "url": f"/web/content/{attachment_id.id}/{attachment_id.name}",
                "target": "new",
            }

    def view_boleto_pdf(self):
        if not self.file_boleto_pdf_id:
            self.generate_boleto_pdf()
        return self._target_new_tab(self.file_boleto_pdf_id)

    def button_cancel(self):
        for record in self:
            if record.payment_mode_id.payment_method_code in BR_CODES_PAYMENT_ORDER:
                for line in record.line_ids:
                    # Verificar a situação do CNAB para apenas apagar
                    # a linha ou mandar uma solicitação de Baixa
                    line.update_cnab_for_cancel_invoice()

        return super().button_cancel()

    def get_invoice_fiscal_number(self):
        """
        Como neste modulo não temos o número do documento fiscal,
        testamos a presença desse campo e se o módulo fiscal não tiver instalado,
        retornamos o name do invoice/account.move do core.
        """
        self.ensure_one()
        if hasattr(self, "document_number") and self.document_number:
            return self.document_number
        return self.name

    def action_post(self):
        result = super().action_post()
        self.load_cnab_info()
        return result

    def load_cnab_info(self):
        # Se não possui Modo de Pagto não há nada a ser feito
        if not self.payment_mode_id:
            return
        # Se o Modo de Pagto é de saída (pgto fornecedor) não há nada a ser feito.
        if self.payment_mode_id.payment_type == "outbound":
            return
        # Se não gera Ordem de Pagto não há nada a ser feito
        if not self.payment_mode_id.payment_order_ok:
            return
        # Podem existir Modo de Pagto q geram Ordens mas não são CNAB
        # por isso nesse caso tbm nada a ser feito
        if self.payment_mode_id.payment_method_code not in BR_CODES_PAYMENT_ORDER:
            return
        # TODO - apesar do campo financial_move_line_ids ser do tipo
        #  compute esta sendo preciso chamar o metodo porque as vezes
        #  ocorre da linha vir vazia o que impede de entrar no FOR
        #  abaixo causando o não preenchimento de dados usados no Boleto,
        #  isso deve ser melhor investigado
        self._compute_financial()
        for index, interval in enumerate(self.financial_move_line_ids):
            inv_number = self.get_invoice_fiscal_number().split("/")[-1]
            numero_documento = inv_number + "/" + str(index + 1).zfill(2)

            sequence = self.payment_mode_id.own_number_sequence_id.next_by_id()

            interval.own_number = (
                sequence if interval.payment_mode_id.generate_own_number else "0"
            )
            interval.document_number = numero_documento
            interval.company_title_identification = hex(interval.id).upper()
            instructions = ""
            if self.eval_payment_mode_instructions:
                instructions = self.eval_payment_mode_instructions + "\n"
            if self.instructions:
                instructions += self.instructions + "\n"
            interval.instructions = instructions
            # Codigo de Instrução do Movimento pode variar,
            # mesmo no CNAB 240
            interval.mov_instruction_code_id = (
                self.payment_mode_id.cnab_sending_code_id.id
            )
        filtered_invoice_ids = self.filtered(
            lambda s: (
                s.payment_mode_id and s.payment_mode_id.auto_create_payment_order
            )
        )
        if filtered_invoice_ids:
            # Criação das Linha na Ordem de Pagamento
            filtered_invoice_ids.create_account_payment_line()

    def unlink(self):
        # Verificar se é necessário solicitar a Baixa no caso de CNAB
        cnab_already_start = False
        for l_aml in self.mapped("line_ids"):
            if l_aml._cnab_already_start():
                # Se exitir um caso já deve ser feito
                cnab_already_start = l_aml._cnab_already_start()
                break

        if cnab_already_start:
            # Solicitar a Baixa do CNAB
            invoice = self.env["account.move"].search([("move_id", "=", self.id)])
            for l_aml in invoice.mapped("financial_move_line_ids"):
                l_aml.update_cnab_for_cancel_invoice()

        return super().unlink()
