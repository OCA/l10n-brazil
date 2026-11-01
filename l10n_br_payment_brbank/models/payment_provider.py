# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from brbank import Capacidade, registro
from brbank.erros import AdapterNaoEncontrado, Validacao

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_bank_connection.models.connection import (
    ADAPTER_LABELS,
    PIX_PROFILE_LABELS,
    capability_flag_labels,
)
from odoo.addons.l10n_br_bank_connection.utils import config as brbank_config

_logger = logging.getLogger(__name__)

BRBANK = "brbank"
# Alias route, for URLs already registered at the banks.
WEBHOOK_ROUTE = "/payment/brbank/webhook"
# Digits of the nosso numero each adapter accepts in `gerar_nosso_numero`.
NOSSO_NUMERO_DIGITS = {
    "banrisul": 8,
    "bb": 10,
    "bradesco": 11,
    "caixa": 15,
    "itau": 8,
    "safra": 9,
    "santander": 12,
}
# Context key: nosso numero reserved per title, by idempotency key.
NOSSO_NUMERO_CONTEXT = "brbank_nosso_numeros"
# Context key: txid of a title by its id at the bank (Bradesco hybrid boleto).
TXID_CONTEXT = "brbank_txids"


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[(BRBANK, "Brazilian bank (brbank)")],
        ondelete={BRBANK: "set default"},
    )
    brbank_adapter = fields.Selection(
        selection="_selection_brbank_adapter",
        string="Bank Adapter",
        help="Adapter of the brbank library that talks to the bank.",
    )
    brbank_pix_perfil = fields.Selection(
        selection="_selection_brbank_pix_perfil",
        string="Pix Profile",
        help="Bank (PSP) of the Pix BACEN adapter.",
    )

    brbank_connection_id = fields.Many2one(
        comodel_name="l10n_br_bank_connection.connection",
        string="Bank Connection",
        domain="[('adapter', '=', brbank_adapter)]",
        ondelete="restrict",
        index=True,
        help="Credentials, token and webhook of the bank account this provider "
        "uses. One connection can serve several providers (boleto and Pix, "
        "for instance).",
    )
    brbank_nosso_numero_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Nosso Numero Sequence",
        readonly=True,
        copy=False,
        help="Created at the first title of a bank whose nosso numero is "
        "chosen by the issuer. Numbers are never reused.",
    )
    brbank_rebate_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Rebate Account",
        check_company=True,
        domain=[
            (
                "account_type",
                "not in",
                ("asset_receivable", "liability_payable", "asset_cash", "off_balance"),
            )
        ],
        help="Account of the credit note posted when the bank accepts a rebate.",
    )
    # What the adapter declares, for the views (O11).
    brbank_capabilities = fields.Char(
        string="Bank Capabilities", compute="_compute_brbank_adapter_info"
    )
    brbank_supports_pdf = fields.Boolean(compute="_compute_brbank_adapter_info")
    brbank_supports_webhook = fields.Boolean(compute="_compute_brbank_adapter_info")
    brbank_supports_instruction = fields.Boolean(compute="_compute_brbank_adapter_info")
    brbank_supports_write_off = fields.Boolean(compute="_compute_brbank_adapter_info")
    brbank_sandbox_validated = fields.Boolean(
        string="Validated in Sandbox", compute="_compute_brbank_adapter_info"
    )
    brbank_is_pix = fields.Boolean(compute="_compute_brbank_adapter_info")
    # === SELECTIONS === #

    @api.model
    def _selection_brbank_adapter(self):
        """Adapters installed in the brbank library (entry points)."""
        return [
            (name, ADAPTER_LABELS.get(name, name))
            for name in registro.listar_adapters()
        ]

    @api.model
    def _selection_brbank_pix_perfil(self):
        try:
            from brbank.adapters.pix_bacen import PERFIS
        except ImportError:  # pragma: no cover
            return []
        return [(name, PIX_PROFILE_LABELS.get(name, name)) for name in sorted(PERFIS)]

    # === COMPUTE METHODS === #

    def _brbank_adapter_class(self):
        self.ensure_one()
        if self.code != BRBANK or not self.brbank_adapter:
            return None
        try:
            return registro.obter_classe(self.brbank_adapter)
        except AdapterNaoEncontrado:
            return None

    @api.depends("code", "brbank_adapter", "brbank_pix_perfil")
    def _compute_brbank_adapter_info(self):
        labels = capability_flag_labels(self.env)
        for provider in self:
            adapter_class = provider._brbank_adapter_class()
            capabilities = (
                adapter_class.capacidades if adapter_class else Capacidade.NENHUMA
            )
            keys = {}
            if adapter_class:
                try:
                    config_cls = brbank_config.config_class(adapter_class)
                    keys = {k["name"]: k for k in brbank_config.describe(config_cls)}
                except brbank_config.ConfigError:
                    keys = {}
            provider.brbank_capabilities = ", ".join(
                label for flag, label in labels.items() if flag in capabilities
            )
            provider.brbank_supports_pdf = Capacidade.PDF in capabilities
            provider.brbank_supports_webhook = Capacidade.WEBHOOK in capabilities
            provider.brbank_supports_instruction = Capacidade.ALTERACAO in capabilities
            provider.brbank_supports_write_off = Capacidade.BAIXA in capabilities
            provider.brbank_sandbox_validated = provider._brbank_validated(
                adapter_class
            )
            provider.brbank_is_pix = "perfil" in keys

    def _brbank_validated(self, adapter_class):
        """Whether the library declares the adapter validated in a sandbox."""
        self.ensure_one()
        if adapter_class is None:
            return False
        if self.brbank_pix_perfil and self.brbank_adapter == "pix_bacen":
            from brbank.adapters.pix_bacen import PERFIS

            profile = PERFIS.get(self.brbank_pix_perfil)
            return bool(profile and profile.validado_sandbox)
        return bool(getattr(adapter_class, "validado_sandbox", False))

    def _compute_feature_support_fields(self):
        """Override of `payment`: a registered title is an `authorized`
        transaction, so brbank providers declare manual capture (capture
        queries the bank, void writes the title off)."""
        res = super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == BRBANK).update(
            {"support_manual_capture": "full_only"}
        )
        return res

    # === CONSTRAINTS === #

    @api.constrains(
        "code",
        "state",
        "brbank_adapter",
        "brbank_pix_perfil",
        "brbank_connection_id",
    )
    def _check_brbank_configuration(self):
        for provider in self.sudo():
            if provider.code != BRBANK or provider.state == "disabled":
                continue
            if not provider.brbank_adapter:
                raise ValidationError(_("Choose the bank adapter of the provider."))
            connection = provider.brbank_connection_id
            if not connection:
                raise ValidationError(
                    _("Choose the bank connection of the provider %s.", provider.name)
                )
            if connection.adapter != provider.brbank_adapter:
                raise ValidationError(
                    _(
                        "The connection %(connection)s uses another bank adapter "
                        "than the provider %(provider)s.",
                        connection=connection.name,
                        provider=provider.name,
                    )
                )
            try:
                provider._brbank_prepare_adapter()
            except UserError as error:
                raise ValidationError(error.args[0]) from error

    @api.onchange("brbank_connection_id")
    def _onchange_brbank_connection_id(self):
        connection = self.brbank_connection_id
        if connection:
            self.brbank_adapter = connection.adapter
            self.brbank_pix_perfil = connection.pix_profile

    # === BUSINESS METHODS: CHECKOUT === #

    @api.model
    def _get_compatible_providers(self, *args, **kwargs):
        """brbank providers never show in the checkout."""
        providers = super()._get_compatible_providers(*args, **kwargs)
        return providers.filtered(lambda p: p.code != BRBANK)

    def _get_supported_currencies(self):
        supported_currencies = super()._get_supported_currencies()
        if self.code == BRBANK:
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name == "BRL"
            )
        return supported_currencies

    def _brbank_payment_method(self):
        """Payment method of the charges: Pix for a Pix profile, boleto otherwise."""
        self.ensure_one()
        code = "pix" if self.brbank_is_pix else "boleto"
        return (
            self.env["payment.method"]
            .with_context(active_test=False)
            ._get_from_code(code)
        )

    # === BUSINESS METHODS: ADAPTER === #

    def _brbank_connection(self):
        """The bank connection of the provider, as the system."""
        self.ensure_one()
        if self.code != BRBANK or not self.brbank_adapter:
            raise UserError(_("This provider is not a brbank provider."))
        connection = self.sudo().brbank_connection_id
        if not connection:
            raise UserError(
                _("The payment provider %s has no bank connection.", self.name)
            )
        return connection

    def _brbank_callbacks(self):
        """Callable keys of the adapter configuration this provider serves."""
        self.ensure_one()
        callbacks = {"obter_txid": dict(self.env.context.get(TXID_CONTEXT) or {}).get}
        number_callback = self._brbank_nosso_numero_callback()
        if number_callback:
            callbacks["gerar_nosso_numero"] = number_callback
        return callbacks

    def _brbank_prepare_adapter(self, callback_outcome=None):
        """Build the adapter class and configuration of the connection."""
        self.ensure_one()
        return self._brbank_connection()._l10n_br_bank_prepare_adapter(
            callbacks=self._brbank_callbacks(), outcome=callback_outcome
        )

    def _brbank_run(self, operation):
        """Call the bank through the connection of the provider."""
        self.ensure_one()
        if self.state == "disabled":
            raise UserError(_("The payment provider %s is disabled.", self.name))
        return self._brbank_connection()._l10n_br_bank_run(
            operation, callbacks=self._brbank_callbacks()
        )

    # === BUSINESS METHODS: NOSSO NUMERO === #

    def _brbank_nosso_numero_digits(self):
        """Digits of the nosso numero the provider generates, or None."""
        self.ensure_one()
        adapter_class = self._brbank_adapter_class()
        if not adapter_class or self.brbank_adapter not in NOSSO_NUMERO_DIGITS:
            return None
        try:
            config_cls = brbank_config.config_class(adapter_class)
        except brbank_config.ConfigError:
            return None
        keys = {key["name"] for key in brbank_config.describe(config_cls)}
        if "gerar_nosso_numero" not in keys:
            return None
        return NOSSO_NUMERO_DIGITS[self.brbank_adapter]

    def _brbank_nosso_numero_start(self, digits):
        """First number of a new sequence, after every number already sent."""
        self.ensure_one()
        txs = (
            self.env["payment.transaction"]
            .sudo()
            .search(
                [
                    ("provider_id", "=", self.id),
                    "|",
                    ("brbank_nosso_numero", "!=", False),
                    ("provider_reference", "!=", False),
                ]
            )
        )
        used = [0]
        for tx in txs:
            value = tx.brbank_nosso_numero or tx.brbank_seu_numero
            if value and value.isdigit() and len(value) <= digits:
                used.append(int(value))
        return max(used) + 1

    def _brbank_nosso_numero_sequence(self, digits):
        self.ensure_one()
        provider = self.sudo()
        if not provider.brbank_nosso_numero_sequence_id:
            provider.brbank_nosso_numero_sequence_id = (
                self.env["ir.sequence"]
                .sudo()
                .create(
                    {
                        "name": _("Nosso numero: %s", provider.name),
                        # A sequence: a number is never given twice, even on rollback.
                        "implementation": "standard",
                        "padding": 0,
                        "number_increment": 1,
                        "number_next": provider._brbank_nosso_numero_start(digits),
                        "company_id": provider.company_id.id,
                    }
                )
            )
        return provider.brbank_nosso_numero_sequence_id

    def _brbank_next_nosso_numero(self):
        """Take the next nosso numero; never truncated, so it cannot repeat."""
        self.ensure_one()
        digits = self._brbank_nosso_numero_digits()
        if not digits:
            return None
        sequence = self._brbank_nosso_numero_sequence(digits)
        number = sequence.next_by_id()
        if not number.isdigit() or len(number) > digits:
            raise UserError(
                _(
                    "The nosso numero sequence of the provider %(name)s reached "
                    "%(number)s, beyond the %(digits)s digits the bank accepts. "
                    "Agree with the bank on a new wallet or agreement before "
                    "issuing more boletos.",
                    name=self.name,
                    number=number,
                    digits=digits,
                )
            )
        return number

    def _brbank_nosso_numero_callback(self):
        """The `gerar_nosso_numero` function of the adapter, or None."""
        self.ensure_one()
        if not self._brbank_nosso_numero_digits():
            return None
        numbers = dict(self.env.context.get(NOSSO_NUMERO_CONTEXT) or {})

        def generate(titulo):
            number = numbers.get(titulo.chave_idempotencia)
            if not number:
                raise Validacao("no nosso numero reserved for this title")
            # Bradesco only takes an int; the other banks take both.
            return int(number)

        return generate
