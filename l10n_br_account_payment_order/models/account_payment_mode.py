# Copyright (C) 2012-Today - KMEE (<http://kmee.com.br>).
#  @author Luis Felipe Miléo - mileo@kmee.com.br
#  @author Renato Lima - renato.lima@akretion.com.br
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import BR_CODES_PAYMENT_ORDER, FORMA_LANCAMENTO, TIPO_SERVICO


class AccountPaymentMode(models.Model):
    _name = "account.payment.mode"
    _inherit = [
        "account.payment.mode",
        "l10n_br_cnab.boleto.fields",
        "l10n_br_cnab.payment.fields",
        "mail.thread",
    ]

    PAYMENT_MODE_DOMAIN = [
        ("dinheiro", _("Dinheiro")),
        ("cheque", _("Cheque")),
        ("pix_transfer", _("PIX Transfer")),
        ("ted", _("TED")),
        ("doc", _("DOC")),
        ("boleto", _("Boleto")),
    ]

    payment_mode_domain = fields.Selection(
        selection=PAYMENT_MODE_DOMAIN,
    )

    auto_create_payment_order = fields.Boolean(
        string="Adicionar automaticamente ao validar a fatura",
        help="Cria a ordem de pagamento automaticamente ao confirmar a fatura",
    )

    service_type = fields.Selection(
        selection=TIPO_SERVICO,
        string="Tipo de Serviço",
        help="Campo G025 do CNAB",
    )

    release_form = fields.Selection(
        selection=FORMA_LANCAMENTO,
        string="Forma Lançamento",
        help="Campo G029 do CNAB",
    )

    cnab_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Sequencia do Arquivo CNAB",
        tracking=True,
    )

    # Fields used to make invisible banks specifics fields
    bank_id = fields.Many2one(
        related="fixed_journal_id.bank_id",
    )

    bank_code_bc = fields.Char(
        related="fixed_journal_id.bank_id.code_bc",
    )

    cnab_processor = fields.Selection(
        selection="_selection_cnab_processor",
    )

    @api.model
    def _selection_cnab_processor(self):
        # Method to be extended by modules that implement CNAB processors.
        return []

    # Codigos de Retorno do Movimento

    # TODO: Campos many2many não estão sendo registrados pelo track_visibility.
    #  Debate no Odoo https://github.com/odoo/odoo/issues/10149
    #  Modulo na OCA v10 que faria isso
    #  https://github.com/OCA/social/tree/10.0/mail_improved_tracking_value
    #  Migração do Modulo para a v12 https://github.com/OCA/social/pull/677
    #  Devemos incluir esse modulo nas Dependencias OCA para poder usa-lo aqui
    #  já que sem ele o campo que armazena os codigos que devem ser usados para
    #  Baixa/Liquidação está sem a rastreabilidade a outra opção seria usar o
    #  modulo auditlog https://github.com/OCA/server-tools/tree/12.0/auditlog.

    # TODO: Ligação com o payment_mode_id não permite extrair para o objeto
    #  l10n_br_cnab.boleto.fields, teria alguma forma de fazer ?
    # Podem existir diferentes codigos, mesmo no 240
    cnab_liq_return_move_code_ids = fields.Many2many(
        comodel_name="l10n_br_cnab.return.move.code",
        relation="l10n_br_cnab_return_liquidity_move_code_rel",
        column1="cnab_liq_return_move_code_id",
        column2="payment_mode_id",
        string="CNAB Liquidity Return Move Code",
        tracking=True,
    )

    @api.constrains(
        "cnab_company_bank_code",
        "cnab_sequence_id",
        "fixed_journal_id",
        "boleto_wallet",
        "group_lines",
    )
    def _check_cnab_restriction(self):
        for record in self:
            if (
                record.payment_method_code not in BR_CODES_PAYMENT_ORDER
                or self.payment_type == "outbound"
            ):
                return False
            fields_forbidden_cnab = []
            if record.group_lines:
                fields_forbidden_cnab.append("Group Lines")

            for field in fields_forbidden_cnab:
                raise ValidationError(
                    _(
                        "The Payment Mode can not be used for CNAB with the field"
                        " %s active. \n Please uncheck it to continue."
                    )
                    % field
                )

            if (
                self.bank_code_bc == "341"
                and self.payment_type == "inbound"
                and not self.boleto_wallet
            ):
                raise ValidationError(_("Carteira no banco Itaú é obrigatória"))

    @api.constrains("boleto_discount_perc")
    def _check_discount_perc(self):
        for record in self:
            if record.boleto_discount_perc > 100 or record.boleto_discount_perc < 0:
                raise ValidationError(
                    _("O percentual deve ser um valor entre 0 a 100.")
                )

    @api.onchange("payment_method_id")
    def _onchange_payment_method_id(self):
        for record in self:
            if record.payment_method_code in BR_CODES_PAYMENT_ORDER:
                # Campos Default que não devem estar marcados no caso CNAB
                record.group_lines = False
                # Selecionavel na Ordem de Pagamento
                record.payment_order_ok = True

    @api.constrains("own_number_sequence_id", "cnab_sequence_id")
    def _check_sequences(self):
        for record in self:
            already_in_use = self.search(
                [
                    ("id", "!=", record.id),
                    "|",
                    ("own_number_sequence_id", "=", record.own_number_sequence_id.id),
                    ("cnab_sequence_id", "=", record.cnab_sequence_id.id),
                ],
                limit=1,
            )

            if already_in_use.own_number_sequence_id:
                raise ValidationError(
                    _(
                        "Sequence Own Number already in use by %(payment_mode)s!",
                        payment_mode=already_in_use.name,
                    )
                )

            if already_in_use.cnab_sequence_id:
                raise ValidationError(
                    _(
                        "Sequence CNAB Sequence already in use by %(payment_mode)s!",
                        payment_mode=already_in_use.name,
                    )
                )
