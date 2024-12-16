# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import BR_CODES_PAYMENT_ORDER, FORMA_LANCAMENTO, TIPO_SERVICO


class L10nBRCNABConfig(models.Model):
    _name = "l10n_br_cnab.config"
    _description = "CNAB Config"
    _inherit = [
        "l10n_br_cnab.boleto.fields",
        "l10n_br_cnab.payment.fields",
        "mail.thread",
    ]

    name = fields.Char(index=True, tracking=True, required=True)

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        ondelete="restrict",
        default=lambda self: self.env.company,
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
        copy=False,
    )

    bank_id = fields.Many2one(
        comodel_name="res.bank",
        tracking=True,
    )

    payment_method_id = fields.Many2one(
        comodel_name="account.payment.method",
        tracking=True,
    )

    bank_code_bc = fields.Char(
        related="bank_id.code_bc",
    )
    payment_method_code = fields.Char(related="payment_method_id.code")
    payment_type = fields.Selection(related="payment_method_id.payment_type")

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
    liq_return_move_code_ids = fields.Many2many(
        comodel_name="l10n_br_cnab.code",
        string="CNAB Liquidity Return Move Code",
        tracking=True,
    )

    comment = fields.Text()

    @api.constrains(
        "cnab_company_bank_code",
        "cnab_sequence_id",
        "boleto_wallet",
    )
    def _check_cnab_restriction(self):
        for record in self:
            if (
                record.payment_method_code not in BR_CODES_PAYMENT_ORDER
                or self.payment_type == "outbound"
            ):
                return False

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

    def _check_sequence_already_in_use(self, field):
        for record in self:
            sequence = getattr(record, f"{field}")
            if sequence:
                already_in_use = record.search(
                    [
                        ("id", "!=", record.id),
                        "|",
                        ("own_number_sequence_id", "=", sequence.id),
                        ("cnab_sequence_id", "=", sequence.id),
                    ],
                    limit=1,
                )
                if already_in_use:
                    raise ValidationError(
                        _(
                            f"Sequence {sequence.name} already in"
                            f" use by {already_in_use.name}!",
                        )
                    )

    @api.constrains("own_number_sequence_id", "cnab_sequence_id")
    def _check_sequences(self):
        self._check_sequence_already_in_use("own_number_sequence_id")
        self._check_sequence_already_in_use("cnab_sequence_id")
