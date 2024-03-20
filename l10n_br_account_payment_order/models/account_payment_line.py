# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    AVISO_FAVORECIDO,
    CODIGO_FINALIDADE_TED,
    COMPLEMENTO_TIPO_SERVICO,
    TIPO_MOVIMENTO,
    TIPO_SERVICO,
)


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

    PIX_TRANSFER_TYPES = [
        ("checking", _("Checking Account (Conta Corrente)")),
        ("saving", _("Saving Account (Conta Poupança)")),
        ("payment", _("Prepaid Payment Account (Conta Pagamento)")),
        ("pix_key", _("Instant Payment Key (Chave Pix)")),
    ]

    digitable_line = fields.Char(
        string="Linha Digitável",
    )

    percent_interest = fields.Float(
        string="Percentual de Juros",
        digits="Account",
    )

    amount_interest = fields.Float(
        string="Valor Juros",
        compute="_compute_interest",
        digits="Account",
    )

    own_number = fields.Char(
        string="Nosso Numero",
    )

    document_number = fields.Char(
        string="Número documento",
    )

    barcode = fields.Char(
        string="Barcode", help="This field is used in the payment of supplier slips"
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

    partner_pix_id = fields.Many2one(
        string="Pix Key",
        comodel_name="res.partner.pix",
    )

    pix_transfer_type = fields.Selection(
        selection=PIX_TRANSFER_TYPES,
        help="Pix transfer type identification",
        compute="_compute_pix_transfer_type",
    )

    service_type = fields.Selection(
        selection=TIPO_SERVICO,
        string="Tipo de Serviço",
        help="Campo G025 do CNAB",
        default="30",
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
        related="order_id.payment_mode_id",
    )

    payment_mode_domain = fields.Selection(
        related="payment_mode_id.payment_mode_domain",
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
        ],
        ondelete={"cnab": "set default"},
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
    move_id = fields.Many2one(comodel_name="account.move", string="Fatura")

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

    def draft2open_payment_line_check(self):
        """
        Override to add brazilian validations
        """
        res = super(AccountPaymentLine, self).draft2open_payment_line_check()
        self._check_pix_transfer_type()
        return res

    @api.onchange("partner_id")
    def partner_id_change(self):
        res = super(AccountPaymentLine, self).partner_id_change()
        partner_pix = False
        if self.partner_id.pix_key_ids:
            partner_pix = self.partner_id.pix_key_ids[0]
        self.partner_pix_id = partner_pix
        return res

    def _compute_pix_transfer_type(self):
        for line in self:
            line.pix_transfer_type = False
            if line.payment_mode_domain != "pix_transfer":
                return
            if line.partner_pix_id:
                line.pix_transfer_type = "pix_key"
            elif line.partner_bank_id:
                acc_type = line.partner_bank_id.transactional_acc_type
                line.pix_transfer_type = acc_type

    def _check_pix_transfer_type(self):
        for rec in self:
            if (
                rec.payment_mode_domain == "pix_transfer"
                and not rec.partner_pix_id
                and not rec.partner_bank_id.transactional_acc_type
            ):
                raise UserError(
                    _(
                        "When the payment method is pix transfer, a pix key must be "
                        "informed, or the bank account with the type of account.\n"
                        f"Payment Line: {rec.name}"
                    )
                )
