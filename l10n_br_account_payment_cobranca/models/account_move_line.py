# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


ESTADOS_CNAB = [
    ("draft", "Inicial"),
    ("added", "Adicionada à ordem de pagamento"),
    ("added_paid", "Adicionada para Baixa"),
    ("exported", "Exportada"),
    ("exporting_error", "Erro ao exportar"),
    ("accepted", "Aceita"),
    ("accepted_hml", "Aceita em Homologação"),
    ("not_accepted", "Não aceita pelo banco"),
    ("done", "Concluído"),
]

SITUACAO_PAGAMENTO = [
    ("inicial", "Inicial"),
    ("aberta", "Aberta"),
    ("paga", "Paga"),
    ("liquidada", "Liquidada"),
    ("baixa", "Baixa Simples"),
    ("baixa_liquidacao", "Baixa por Liquidação em Dinheiro"),
]


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    state_cnab = fields.Selection(ESTADOS_CNAB, "Estados CNAB", default="draft")
    date_payment_created = fields.Date("Data da criação do pagamento", readonly=True)
    nosso_numero = fields.Char(string="Nosso Numero")
    numero_documento = fields.Char(string="Número documento")
    identificacao_titulo_empresa = fields.Char(string="Identificação Titulo Empresa")
    situacao_pagamento = fields.Selection(
        selection=SITUACAO_PAGAMENTO, string="Situação do Pagamento", default="inicial"
    )
    instrucoes = fields.Text(string="Instruções de cobrança", readonly=True)

    residual = fields.Monetary(
        string="Valor Residual", default=0.0, currency_field="company_currency_id"
    )

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        vals = super(AccountMoveLine, self)._prepare_payment_line_vals(payment_order)
        vals["nosso_numero"] = self.nosso_numero
        vals["numero_documento"] = self.numero_documento
        vals["identificacao_titulo_empresa"] = self.identificacao_titulo_empresa

        if self.invoice_id.state == "paid":
            vals["amount_currency"] = self.credit or self.debit

        return vals

    @api.multi
    def create_payment_line_from_move_line(self, payment_order):
        """
        Altera estado do cnab para adicionado a ordem
        :param payment_order:
        :return:
        """
        state_cnab = "added"
        if self.invoice_id.state == "paid":
            state_cnab = "added_paid"

        self.state_cnab = state_cnab

        return super(AccountMoveLine, self).create_payment_line_from_move_line(
            payment_order
        )

    @api.multi
    def generate_boleto(self, validate=True):
        raise NotImplementedError

    @api.multi
    def _update_check(self):

        if self._context.get("reprocessing"):
            return True

        return super(AccountMoveLine, self)._update_check()

    @api.multi
    def write(self, vals):
        """
        Sobrescrita do método Write. Não deve ser possível voltar o state_cnab
        ou a situacao_pagamento para um estado anterior
        :param vals:
        :return:
        """
        state_cnab = vals.get("state_cnab")

        if state_cnab and (
            self.state_cnab == "done"
            or (
                self.state_cnab in ["accepted", "accepted_hml"]
                and state_cnab not in ["accepted", "accepted_hml", "done"]
            )
        ):
            vals.pop("state_cnab", False)

        if self.situacao_pagamento not in ["inicial", "aberta"]:
            vals.pop("situacao_pagamento", False)

        return super(AccountMoveLine, self).write(vals)
