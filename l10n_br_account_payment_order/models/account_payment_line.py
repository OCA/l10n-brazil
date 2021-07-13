# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons import decimal_precision as dp

from ..constants import (
    AVISO_FAVORECIDO,
    CODIGO_FINALIDADE_TED,
    COMPLEMENTO_TIPO_SERVICO,
    TIPO_MOVIMENTO,
)


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

    digitable_line = fields.Char(
        string="Linha Digitável",
    )

    percent_interest = fields.Float(
        string="Percentual de Juros",
        digits=dp.get_precision("Account"),
    )

    amount_interest = fields.Float(
        string="Valor Juros",
        compute="_compute_interest",
        digits=dp.get_precision("Account"),
    )

    own_number = fields.Char(
        string="Nosso Numero",
    )

    document_number = fields.Char(
        string="Número documento",
    )

    company_title_identification = fields.Char(
        string="Identificação Titulo Empresa",
    )

    doc_finality_code = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string="Complemento do Tipo de Serviço",
        help="Campo P005 do CNAB",
    )

    ted_finality_code = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string="Código Finalidade da TED",
        help="Campo P011 do CNAB",
    )

    complementary_finality_code = fields.Char(
        string="Código de finalidade complementar",
        size=2,
        help="Campo P013 do CNAB",
    )

    favored_warning = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string="Aviso ao Favorecido",
        help="Campo P006 do CNAB",
        default="0",
    )

    rebate_value = fields.Monetary(
        string="Valor do Abatimento",
        help="Campo G045 do CNAB",
    )

    discount_value = fields.Monetary(
        string="Valor do Desconto",
        help="Campo G046 do CNAB",
    )

    interest_value = fields.Monetary(
        string="Valor da Mora",
        help="Campo G047 do CNAB",
    )

    fee_value = fields.Monetary(
        string="Valor da Multa",
        help="Campo G048 do CNAB",
    )

    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        track_visibility="onchange",
    )

    # Campo não usado no BRCobranca
    movement_type = fields.Selection(
        selection=TIPO_MOVIMENTO,
        string="Tipo de Movimento",
        help="Campo G060 do CNAB",
        default="0",
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

    communication_type = fields.Selection(
        selection_add=[
            ("cnab", "CNAB"),
        ]
    )

    # No caso de Ordens de Pagto vinculadas devido o
    # ondelete=restrict no campo move_line_id do account.payment.line
    # não é possível apagar uma move que já tenha uma Ordem de
    # Pagto confirmada ( processo chamado pelo action_cancel objeto
    # account.invoice ), acontece o erro abaixo de constraint:
    # psycopg2.IntegrityError: update or delete on table
    # "account_move_line" violates foreign key constraint
    # "account_payment_line_move_line_id_fkey" on table
    # "account_payment_line"
    # TODO: Verificar a possibilidade de alteração no
    #  modulo account_payment_order na v14
    move_line_id = fields.Many2one(ondelete=None)
    ml_maturity_date = fields.Date(related=None)
    # Para manter a rastreabilidade está sendo adicionado uma relação
    # com a account.invoice referente, já que a AML pode ser apagada
    invoice_id = fields.Many2one(comodel_name="account.invoice", string="Fatura")

    @api.depends("percent_interest", "amount_currency", "currency_id")
    def _compute_interest(self):
        for record in self:
            record.amount_interest = record.currency_id.round(
                record.amount_currency * (record.percent_interest / 100)
            )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        mode = (
            self.env["account.payment.order"]
            .browse(self.env.context.get("order_id"))
            .payment_mode_id
        )
        if mode.doc_finality_code:
            res.update({"doc_finality_code": mode.doc_finality_code})
        if mode.ted_finality_code:
            res.update({"ted_finality_code": mode.ted_finality_code})
        if mode.complementary_finality_code:
            res.update(
                {"complementary_finality_code": mode.complementary_finality_code}
            )
        if mode.favored_warning:
            res.update({"favored_warning": mode.favored_warning})

        return res
