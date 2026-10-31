# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from brbank.pagamento import CapacidadePagamento

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_bank_connection.utils import config as bank_config

# Without LIBERACAO the capabilities cannot tell whether a payment waits for an
# approval in the bank channel. Any other adapter gets the strongest warning.
NO_API_RELEASE_NOTICE = {
    "itau": "bank_approval",
    "inter": "account_setting",
}


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    api_provider = fields.Selection(
        selection_add=[("brbank", "brbank (Brazilian banks)")],
        ondelete={"brbank": "set null"},
    )
    bank_connection_id = fields.Many2one(
        comodel_name="l10n_br_bank_connection.connection",
        string="Bank Connection",
        check_company=True,
    )
    brbank_contract = fields.Char(
        string="Payment Contract",
        help="Payment agreement of the company at the bank (PGT at Banco do Brasil).",
    )
    brbank_payment_kind = fields.Selection(
        selection=[
            ("126", "Suppliers"),
            ("127", "Salaries"),
            ("128", "Other"),
        ],
        string="Kind of Payments",
        default="126",
    )
    brbank_ted_purpose = fields.Integer(
        string="TED Purpose Code",
        help="Purpose code sent with TED transfers to other banks (bank table).",
    )
    api_require_second_factor = fields.Boolean(
        compute="_compute_api_require_second_factor", store=True, readonly=False
    )
    brbank_uses_contract = fields.Boolean(compute="_compute_brbank_info")
    brbank_uses_ted_purpose = fields.Boolean(compute="_compute_brbank_info")
    brbank_send_notice = fields.Selection(
        selection=[
            ("authorize_in_odoo", "The bank waits for the authorization from Odoo"),
            ("bank_approval", "Waits for the approval at the bank"),
            ("account_setting", "Depends on the approval setting of the account"),
            ("pays_on_send", "Paid when the bank receives it"),
        ],
        string="What Sending Does",
        compute="_compute_brbank_info",
    )

    @api.depends("api_provider", "bank_connection_id.adapter")
    def _compute_api_require_second_factor(self):
        for mode in self:
            mode.api_require_second_factor = (
                mode.api_require_second_factor or mode._brbank_money_moves_from_odoo()
            )

    def _brbank_money_moves_from_odoo(self):
        """No separate approval at the bank: the Odoo click is what pays."""
        self.ensure_one()
        return self.brbank_send_notice in (
            "authorize_in_odoo",
            "account_setting",
            "pays_on_send",
        )

    @api.depends("api_provider", "bank_connection_id.adapter")
    def _compute_brbank_info(self):
        for mode in self:
            mode.brbank_uses_contract = False
            mode.brbank_uses_ted_purpose = False
            mode.brbank_send_notice = False
            connection = mode.bank_connection_id
            capabilities = mode._brbank_capabilities()
            if not capabilities:
                continue
            keys = {
                key["name"]: key
                for key in bank_config.describe(
                    bank_config.config_class(
                        connection._l10n_br_bank_payment_adapter_class()
                    )
                )
            }
            mode.brbank_uses_contract = "contrato" in keys
            mode.brbank_uses_ted_purpose = (
                "finalidade_ted" in keys
                or keys.get("ted_finalidade", {}).get("type") is int
            )
            if (
                CapacidadePagamento.LIBERACAO | CapacidadePagamento.LOTE_LOCAL
            ) in capabilities:
                mode.brbank_send_notice = "authorize_in_odoo"
            elif CapacidadePagamento.LIBERACAO in capabilities:
                mode.brbank_send_notice = "bank_approval"
            else:
                mode.brbank_send_notice = NO_API_RELEASE_NOTICE.get(
                    connection.adapter, "pays_on_send"
                )

    def _brbank_capabilities(self):
        self.ensure_one()
        if self.api_provider != "brbank" or not self.bank_connection_id:
            return CapacidadePagamento.NENHUMA
        return self.bank_connection_id._l10n_br_bank_payment_capabilities()

    @api.constrains(
        "api_provider",
        "bank_connection_id",
        "brbank_contract",
        "api_require_second_factor",
    )
    def _check_brbank(self):
        for mode in self.filtered(lambda m: m.api_provider == "brbank"):
            if not mode.bank_connection_id:
                raise ValidationError(
                    _(
                        "Payment mode %s sends through brbank: set the bank "
                        "connection.",
                        mode.name,
                    )
                )
            mode.bank_connection_id._l10n_br_bank_payment_adapter_class()
            if mode._brbank_money_moves_from_odoo() and (
                not mode.api_require_second_factor
            ):
                raise ValidationError(
                    _(
                        "Payment mode %s moves money from Odoo, with no approval "
                        "at the bank: it requires the second factor.",
                        mode.name,
                    )
                )
            if mode.brbank_uses_contract and not mode.brbank_contract:
                raise ValidationError(
                    _(
                        "Payment mode %s sends through this bank: set the payment "
                        "contract.",
                        mode.name,
                    )
                )
