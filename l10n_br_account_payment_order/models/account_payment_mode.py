# Copyright (C) 2012-Today - KMEE (<http://kmee.com.br>).
#  @author Luis Felipe Miléo - mileo@kmee.com.br
#  @author Renato Lima - renato.lima@akretion.com.br
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import BR_CODES_PAYMENT_ORDER


class AccountPaymentMode(models.Model):
    _name = "account.payment.mode"
    _inherit = [
        "account.payment.mode",
        "mail.thread",
    ]

    cnab_config_id = fields.Many2one(
        comodel_name="l10n_br_cnab.config",
        string="CNAB Config",
        tracking=True,
    )

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

    # Fields used to make invisible banks specifics fields
    bank_id = fields.Many2one(
        related="fixed_journal_id.bank_id",
    )

    bank_code_bc = fields.Char(
        related="fixed_journal_id.bank_id.code_bc",
    )

    # TODO: Necessário adaptar o modulo l10n_br_cnab_structure
    #  para a Separação da Configuração CNAB do Modo de Pagto
    cnab_processor = fields.Selection(
        selection="_selection_cnab_processor",
    )

    @api.model
    def _selection_cnab_processor(self):
        # Method to be extended by modules that implement CNAB processors.
        return []

    @api.constrains(
        "fixed_journal_id",
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

    @api.onchange("payment_method_id")
    def _onchange_payment_method_id(self):
        for record in self:
            if record.payment_method_code in BR_CODES_PAYMENT_ORDER:
                # Campos Default que não devem estar marcados no caso CNAB
                record.group_lines = False
                # Selecionavel na Ordem de Pagamento
                record.payment_order_ok = True
