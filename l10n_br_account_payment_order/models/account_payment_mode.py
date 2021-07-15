# Copyright (C) 2012-Today - KMEE (<http://kmee.com.br>).
#  @author Luis Felipe Miléo - mileo@kmee.com.br
#  @author Renato Lima - renato.lima@akretion.com.br
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import BR_CODES_PAYMENT_ORDER, FORMA_LANCAMENTO, TIPO_SERVICO


class AccountPaymentMode(models.Model):
    _name = "account.payment.mode"
    _inherit = [
        "account.payment.mode",
        "mail.thread",
        "l10n_br_cnab.boleto.fields",
        "l10n_br_cnab.payment.fields",
    ]

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
        track_visibility="always",
    )

    # Fields used to make invisible banks specifics fields
    bank_id = fields.Many2one(
        related="fixed_journal_id.bank_id",
    )

    bank_code_bc = fields.Char(
        related="fixed_journal_id.bank_id.code_bc",
    )

    own_number_type = fields.Selection(
        related="fixed_journal_id.company_id.own_number_type",
    )

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
        track_visibility="always",
    )

    @api.constrains(
        "code_convetion",
        "cnab_sequence_id",
        "fixed_journal_id",
        "boleto_wallet",
        "group_lines",
        "generate_move",
        "post_move",
    )
    def _check_cnab_restriction(self):
        for record in self:
            if record.payment_method_code not in BR_CODES_PAYMENT_ORDER:
                return False
            fields_forbidden_cnab = []
            if record.group_lines:
                fields_forbidden_cnab.append("Group Lines")
            if record.generate_move:
                fields_forbidden_cnab.append("Generated Moves")
            if record.post_move:
                fields_forbidden_cnab.append("Post Moves")

            for field in fields_forbidden_cnab:
                raise ValidationError(
                    _(
                        "The Payment Mode can not be used for CNAB with the field"
                        " %s active. \n Please uncheck it to continue."
                    )
                    % field
                )

            if self.bank_code_bc == "341" and not self.boleto_wallet:
                raise ValidationError(_("Carteira no banco Itaú é obrigatória"))

    @api.onchange("product_tax_id")
    def _onchange_product_tax_id(self):
        if not self.product_tax_id:
            self.tax_account_id = False

    def get_own_number_sequence(self, inv, numero_documento):
        if inv.company_id.own_number_type == "0":
            # SEQUENCIAL_EMPRESA
            sequence = inv.company_id.own_number_sequence_id.next_by_id()
        elif inv.company_id.own_number_type == "1":
            # SEQUENCIAL_FATURA
            sequence = numero_documento.replace("/", "")
        elif inv.company_id.own_number_type == "2":
            # SEQUENCIAL_CARTEIRA
            sequence = inv.payment_mode_id.own_number_sequence_id.next_by_id()
        else:
            raise UserError(
                _(
                    "Favor acessar aba Cobrança da configuração da"
                    " sua empresa para determinar o tipo de "
                    "sequencia utilizada nas cobrancas"
                )
            )

        return sequence

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
                record.generate_move = False
                record.post_move = False
                # Selecionavel na Ordem de Pagamento
                record.payment_order_ok = True

    @api.constrains("own_number_sequence_id")
    def _check_own_number_sequence_id(self):
        for record in self:
            already_in_use = record.search(
                [
                    ("id", "!=", record.id),
                    ("own_number_sequence_id", "=", record.own_number_sequence_id.id),
                ],
                limit=1,
            )
            if already_in_use:
                raise ValidationError(
                    _("Sequence Own Number already in use by %s.") % already_in_use.name
                )

    @api.constrains("cnab_sequence_id")
    def _check_cnab_sequence_id(self):
        for record in self:
            already_in_use = record.search(
                [
                    ("id", "!=", record.id),
                    ("cnab_sequence_id", "=", record.cnab_sequence_id.id),
                ]
            )

            if already_in_use:
                raise ValidationError(
                    _("Sequence CNAB Sequence already in use by %s.")
                    % already_in_use.name
                )
