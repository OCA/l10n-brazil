# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import hashlib
import importlib
import inspect
import json
import logging
import re
import secrets
from datetime import timedelta

import httpx
import psycopg2
from brbank import Capacidade, registro
from brbank.erros import AdapterNaoEncontrado, ErroBrbank, Indisponivel

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..utils import config as bank_config
from ..utils.runner import run_in_dedicated_loop
from ..utils.token_store import OdooTokenStore, read_refresh_token

_logger = logging.getLogger(__name__)

WEBHOOK_ROUTE = "/l10n_br_bank_connection/webhook"
OAUTH_START_ROUTE = "/l10n_br_bank_connection/oauth/start"
OAUTH_CALLBACK_ROUTE = "/l10n_br_bank_connection/oauth/callback"
ADMIN_GROUP = "l10n_br_bank_connection.group_bank_connection_admin"
SECRET_GROUP = "base.group_system"
OAUTH_VALIDITY = timedelta(minutes=10)
# Lock timeout (ms) of a write made apart: the caller waits for it.
APART_LOCK_TIMEOUT_MS = 5000
# Key of `cr.cache` with the refresh tokens renewed in the current transaction.
RENEWED_TOKENS = "l10n_br_bank_renewed_refresh_tokens"
# The configuration requires a refresh token before the consent is done.
PENDING_REFRESH_TOKEN = "pending-authorization"

ADAPTER_LABELS = {
    "banrisul": "Banrisul (041)",
    "bb": "Banco do Brasil (001)",
    "bradesco": "Bradesco (237)",
    "btg": "BTG Pactual (208)",
    "c6": "C6 Bank (336)",
    "caixa": "Caixa (104)",
    "inter": "Banco Inter (077)",
    "itau": "Itaú (341)",
    "pinbank": "PinBank",
    "pix_bacen": "Pix (BACEN API)",
    "safra": "Safra (422)",
    "santander": "Santander (033)",
    "sicoob": "Sicoob (756)",
    "sicredi": "Sicredi (748)",
    "unicred": "Unicred (136)",
}
PIX_PROFILE_LABELS = {
    "bb": "Banco do Brasil",
    "bradesco": "Bradesco",
    "efi": "Efí",
    "inter": "Banco Inter",
    "itau": "Itaú",
    "santander": "Santander",
    "sicoob": "Sicoob",
    "sicredi": "Sicredi",
}
# Field of the connection -> key used by the adapter configurations.
GENERIC_FIELDS = {
    "client_id": "client_id",
    "client_secret": "client_secret",
    "username": "usuario",
    "password": "senha",
    "certificate": "certificado_pem",
    "private_key": "chave_pem",
    "pix_key": "chave_pix",
    "refresh_token": "refresh_token",
    "api_base_url_override": "url_base_override",
    "token_url_override": "url_token_override",
    "scopes": "escopos_dda",
}
STATE_COLORS = {"ok": 10, "warning": 2, "error": 1}


def capability_flag_labels(env):
    return {
        Capacidade.HIBRIDO: env._("Hybrid boleto (Pix QR code)"),
        Capacidade.SO_HIBRIDO: env._("Hybrid boleto only"),
        Capacidade.ALTERACAO: env._("Instructions (due date, rebate)"),
        Capacidade.BAIXA: env._("Write-off"),
        Capacidade.PDF: env._("Boleto PDF"),
        Capacidade.WEBHOOK: env._("Webhook"),
        Capacidade.PIX_COB: env._("Immediate Pix charge"),
        Capacidade.PIX_COBV: env._("Pix charge with due date"),
        Capacidade.EMISSAO_ASSINCRONA: env._("Asynchronous registration"),
        Capacidade.INSTRUCAO_ASSINCRONA: env._("Asynchronous instructions"),
        Capacidade.CNAB_REMESSA: env._("CNAB remittance"),
    }


def _normalize_cnpj(value):
    """CNPJ without punctuation; letters kept (alphanumeric CNPJ), uppercase."""
    return re.sub(r"[^0-9A-Za-z]", "", value or "").upper()


def _pkce_challenge(verifier):
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _save_refresh_token(registry, connection_id, token):
    """Commit a renewed refresh token in a transaction of its own."""
    try:
        with registry.cursor() as cr:
            cr.execute(
                "SET LOCAL lock_timeout = %s",
                (f"{int(APART_LOCK_TIMEOUT_MS)}ms",),
                log_exceptions=False,
            )
            cr.execute(
                "SELECT id FROM l10n_br_bank_connection_connection "
                "WHERE id = %s FOR UPDATE",
                (connection_id,),
                log_exceptions=False,
            )
            if not cr.fetchone():
                # Connection created in the caller transaction, not committed.
                return "connection not committed yet"
            cr.execute(
                "UPDATE l10n_br_bank_connection_connection "
                "SET refresh_token = %s, write_date = now() AT TIME ZONE 'UTC' "
                "WHERE id = %s",
                (token, connection_id),
                log_exceptions=False,
            )
        return None
    except psycopg2.Error as error:
        return type(error).__name__


class IncompleteConfiguration(UserError):
    """Required keys missing: tolerated while the connection is a draft."""


class BankConnection(models.Model):
    """A connection to a bank, shared by every domain that talks to it."""

    _name = "l10n_br_bank_connection.connection"
    _description = "Bank Connection"
    _inherit = ["mail.thread"]
    _order = "name, id"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    cnpj = fields.Char(
        string="CNPJ",
        compute="_compute_cnpj",
        store=True,
        readonly=False,
        help="CNPJ of the account holder, as the bank knows it. Defaults to the "
        "CNPJ of the company.",
    )
    adapter = fields.Selection(
        selection="_selection_adapter",
        required=True,
        help="Adapter of the brbank library that talks to the bank.",
    )
    pix_profile = fields.Selection(
        selection="_selection_pix_profile",
        help="Bank (PSP) of the Pix BACEN adapter.",
    )
    environment = fields.Selection(
        selection=[("test", "Test (bank sandbox)"), ("prod", "Production")],
        required=True,
        default="test",
        tracking=True,
    )
    api_base_url_override = fields.Char(
        string="API URL Override",
        help="Points the adapter to another server (bank simulator, tests). "
        "Leave empty to use the bank environment.",
    )
    token_url_override = fields.Char(
        string="Token URL Override",
        help="Same for the OAuth token endpoint.",
    )

    # Credentials: readable by system administrators only.
    client_id = fields.Char(string="Client ID", groups=SECRET_GROUP)
    client_secret = fields.Char(groups=SECRET_GROUP)
    username = fields.Char(string="API Username", groups=SECRET_GROUP)
    password = fields.Char(string="API Password", groups=SECRET_GROUP)
    certificate = fields.Binary(
        string="Certificate (PEM)",
        attachment=False,
        groups=SECRET_GROUP,
        help="mTLS certificate. It only goes to a temporary file in memory "
        "while the TLS context is built.",
    )
    private_key = fields.Binary(
        string="Private Key (PEM)", attachment=False, groups=SECRET_GROUP
    )
    pix_key = fields.Char(groups=SECRET_GROUP)
    refresh_token = fields.Char(
        groups=SECRET_GROUP,
        copy=False,
        help="OAuth refresh token obtained at the bank (authorization code "
        "flow, see Connect). The bank may return a new one at each renewal: "
        "the connection keeps it up to date by itself.",
    )
    extra_config = fields.Text(
        string="Extra Settings",
        groups=SECRET_GROUP,
        help="JSON object with the bank specific settings (agreement, wallet, "
        "client number...). Use 'Fill settings template' to get the keys.",
    )
    secret_config = fields.Text(
        string="Extra Secrets",
        groups=SECRET_GROUP,
        help="JSON object with the bank specific secrets (developer key, API "
        "key, webhook secret...).",
    )
    scopes = fields.Char(
        groups=SECRET_GROUP,
        help="OAuth scopes asked at the consent. Empty uses the default of "
        "the adapter.",
    )
    webhook_token = fields.Char(
        groups=SECRET_GROUP,
        copy=False,
        default=lambda self: secrets.token_urlsafe(32),
    )
    webhook_url = fields.Char(
        compute="_compute_webhook_url", groups=SECRET_GROUP, string="Webhook URL"
    )

    state = fields.Selection(
        selection=[
            ("draft", "Not Connected"),
            ("connected", "Connected"),
            ("error", "Error"),
            ("needs_reconsent", "Needs Reconsent"),
        ],
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    last_error = fields.Text(readonly=True, copy=False)
    sync_status_ids = fields.One2many(
        comodel_name="l10n_br_bank_connection.sync_status",
        inverse_name="connection_id",
        string="Synchronization",
        readonly=True,
    )
    oauth_state = fields.Char(groups=SECRET_GROUP, copy=False)
    oauth_verifier = fields.Char(groups=SECRET_GROUP, copy=False)
    oauth_expires = fields.Datetime(groups=SECRET_GROUP, copy=False)

    # What the adapter declares, for the views.
    capability_labels = fields.Char(compute="_compute_adapter_info")
    sandbox_validated = fields.Boolean(compute="_compute_adapter_info")
    oauth_supported = fields.Boolean(compute="_compute_adapter_info")
    uses_client_id = fields.Boolean(compute="_compute_adapter_info")
    uses_client_secret = fields.Boolean(compute="_compute_adapter_info")
    uses_username = fields.Boolean(compute="_compute_adapter_info")
    uses_password = fields.Boolean(compute="_compute_adapter_info")
    uses_certificate = fields.Boolean(compute="_compute_adapter_info")
    uses_pix_key = fields.Boolean(compute="_compute_adapter_info")
    uses_refresh_token = fields.Boolean(compute="_compute_adapter_info")
    is_pix = fields.Boolean(compute="_compute_adapter_info")
    settings_help = fields.Text(compute="_compute_adapter_info")

    # === SELECTIONS === #

    @api.model
    def _selection_adapter(self):
        """Adapters installed in the brbank library (entry points)."""
        return [
            (name, ADAPTER_LABELS.get(name, name))
            for name in registro.listar_adapters()
        ]

    @api.model
    def _selection_pix_profile(self):
        try:
            from brbank.adapters.pix_bacen import PERFIS
        except ImportError:  # pragma: no cover
            return []
        return [(name, PIX_PROFILE_LABELS.get(name, name)) for name in sorted(PERFIS)]

    # === COMPUTE METHODS === #

    def _l10n_br_bank_adapter_class(self):
        self.ensure_one()
        if not self.adapter:
            return None
        try:
            return registro.obter_classe(self.adapter)
        except AdapterNaoEncontrado:
            return None

    @api.model
    def _l10n_br_bank_company_cnpj(self, company):
        return _normalize_cnpj(company.partner_id.vat)

    @api.depends("company_id")
    def _compute_cnpj(self):
        for connection in self:
            if not connection.cnpj:
                connection.cnpj = self._l10n_br_bank_company_cnpj(connection.company_id)

    @api.depends("adapter", "pix_profile")
    def _compute_adapter_info(self):
        labels = capability_flag_labels(self.env)
        required_label = _(" (required)")
        secret_label = _(" [secret]")
        for connection in self:
            adapter_class = connection._l10n_br_bank_adapter_class()
            capabilities = (
                adapter_class.capacidades if adapter_class else Capacidade.NENHUMA
            )
            keys = {}
            if adapter_class:
                try:
                    config_cls = bank_config.config_class(adapter_class)
                    keys = {k["name"]: k for k in bank_config.describe(config_cls)}
                except bank_config.ConfigError:
                    keys = {}
            names = [label for flag, label in labels.items() if flag in capabilities]
            if connection._l10n_br_bank_dda_capable(adapter_class):
                names.append(_("DDA (authorized direct debits)"))
            connection.capability_labels = ", ".join(names)
            connection.sandbox_validated = connection._l10n_br_bank_validated(
                adapter_class
            )
            connection.oauth_supported = bool(
                connection._l10n_br_bank_oauth_functions()
            )
            connection.uses_client_id = "client_id" in keys
            connection.uses_client_secret = "client_secret" in keys
            connection.uses_username = "usuario" in keys
            connection.uses_password = "senha" in keys
            connection.uses_certificate = "certificado_pem" in keys
            connection.uses_pix_key = "chave_pix" in keys
            connection.uses_refresh_token = "refresh_token" in keys
            connection.is_pix = "perfil" in keys
            connection.settings_help = "\n".join(
                "{name}: {kind}{required}{secret}".format(
                    name=key["name"],
                    kind=getattr(key["type"], "__name__", "json"),
                    required=required_label if key["required"] else "",
                    secret=secret_label if key["secret"] else "",
                )
                for key in keys.values()
                if not key["generic"] and not key["callable"]
            )

    @staticmethod
    def _l10n_br_bank_dda_capable(adapter_class):
        """Whether the adapter takes part in DDA."""
        if adapter_class is None:
            return False
        try:
            from brbank.dda import AdapterDda, CapacidadeDda
        except ImportError:
            return False
        return issubclass(adapter_class, AdapterDda) and bool(
            getattr(adapter_class, "capacidades_dda", CapacidadeDda.NENHUMA)
        )

    def _l10n_br_bank_validated(self, adapter_class):
        """Whether the library declares the adapter validated in a sandbox."""
        self.ensure_one()
        if adapter_class is None:
            return False
        if self.pix_profile and self.adapter == "pix_bacen":
            from brbank.adapters.pix_bacen import PERFIS

            profile = PERFIS.get(self.pix_profile)
            return bool(profile and profile.validado_sandbox)
        return bool(getattr(adapter_class, "validado_sandbox", False))

    @api.depends("webhook_token")
    def _compute_webhook_url(self):
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        )
        for connection in self:
            if not connection.id:
                connection.webhook_url = False
                continue
            connection.webhook_url = "{}{}/{}/{}".format(
                base_url.rstrip("/"),
                WEBHOOK_ROUTE,
                connection.id,
                connection.webhook_token or "",
            )

    # === CONSTRAINTS === #

    @api.constrains(
        "adapter",
        "pix_profile",
        "environment",
        "state",
        "extra_config",
        "secret_config",
    )
    def _check_configuration(self):
        for connection in self.sudo():
            connection._l10n_br_bank_load_json("extra_config")
            connection._l10n_br_bank_load_json("secret_config")
            if not connection.adapter:
                continue
            try:
                connection._l10n_br_bank_prepare_adapter()
            except IncompleteConfiguration as error:
                # A draft may be incomplete, a connected one may not.
                if connection.state != "draft":
                    raise ValidationError(error.args[0]) from error
            except UserError as error:
                raise ValidationError(error.args[0]) from error

    def _l10n_br_bank_load_json(self, field_name):
        """Read a JSON settings field as a dict."""
        self.ensure_one()
        text = self.sudo()[field_name]
        if not text or not text.strip():
            return {}
        try:
            value = json.loads(text)
        except ValueError:
            value = None
        if not isinstance(value, dict):
            raise ValidationError(
                _(
                    "The field %s must hold a JSON object.",
                    self._fields[field_name].string,
                )
            )
        return value

    # === ADAPTER === #

    def _l10n_br_bank_prepare_adapter(self, callbacks=None, outcome=None, oauth=False):
        """Build the adapter class and configuration of the connection."""
        self.ensure_one()
        connection = self.sudo()
        adapter_class = connection._l10n_br_bank_adapter_class()
        if adapter_class is None:
            raise UserError(
                _(
                    "The bank adapter %s is not installed in the brbank library.",
                    connection.adapter,
                )
            )
        generic = {
            "conta": f"odoo-connection-{connection.id}",
            "ambiente": "sandbox" if connection.environment == "test" else "producao",
            "perfil": connection.pix_profile,
            "cnpj_empresa": _normalize_cnpj(connection.cnpj),
        }
        for field_name, key in GENERIC_FIELDS.items():
            value = connection[field_name]
            if value and connection._fields[field_name].type == "binary":
                value = base64.b64decode(value)
            generic[key] = value
        renewed = self.env.cr.cache.get(RENEWED_TOKENS, {}).get(connection.id)
        if renewed:
            generic["refresh_token"] = renewed
        try:
            config_cls = bank_config.config_class(adapter_class)
            keys = {key["name"] for key in bank_config.describe(config_cls)}
            if connection.environment == "test" and "ambiente" not in keys:
                raise UserError(
                    _(
                        "The bank adapter %s has no test environment: every call "
                        "reaches production. Use the production environment and "
                        "validate it with a low amount.",
                        connection.adapter,
                    )
                )
            if oauth and "refresh_token" in keys and not generic.get("refresh_token"):
                generic["refresh_token"] = PENDING_REFRESH_TOKEN
            served = connection._l10n_br_bank_served_callbacks(
                keys, generic, outcome if outcome is not None else {}
            )
            served.update({k: v for k, v in (callbacks or {}).items() if k in keys})
            config = bank_config.build(
                config_cls,
                generic,
                connection._l10n_br_bank_load_json("extra_config"),
                connection._l10n_br_bank_load_json("secret_config"),
                callbacks=served,
            )
        except bank_config.ConfigError as error:
            parts = []
            if error.missing:
                parts.append(_("missing: %s", ", ".join(error.missing)))
            if error.unknown:
                parts.append(_("unknown or invalid: %s", ", ".join(error.unknown)))
            if error.misplaced:
                parts.append(
                    _(
                        "secrets typed in Extra Settings, move them to Extra "
                        "Secrets: %s",
                        ", ".join(error.misplaced),
                    )
                )
            message = _(
                "Incomplete configuration of the connection %(name)s (%(details)s).",
                name=connection.name,
                details="; ".join(parts),
            )
            if error.missing and not (error.unknown or error.misplaced):
                raise IncompleteConfiguration(message) from error
            raise UserError(message) from error
        except ErroBrbank as error:
            raise UserError(
                _(
                    "The bank refused the configuration of the connection "
                    "%(name)s: %(error)s",
                    name=connection.name,
                    error=error,
                )
            ) from error
        return adapter_class, config

    def _l10n_br_bank_served_callbacks(self, keys, generic, outcome):
        """Functions and objects this module serves to the adapter."""
        self.ensure_one()
        served = {}
        if not self.id:
            return served
        registry = self.env.registry
        connection_id = self.id
        if "ao_renovar_refresh_token" in keys:
            served["ao_renovar_refresh_token"] = self._l10n_br_bank_refresh_callback(
                outcome
            )
        if "armazem" in keys:
            served["armazem"] = OdooTokenStore(registry, connection_id)
        if "ler_refresh_token" in keys:
            initial = generic.get("refresh_token")

            def read():
                return read_refresh_token(registry, connection_id, initial)

            served["ler_refresh_token"] = read
        return served

    def _l10n_br_bank_http_transport(self):
        """HTTP transport of the adapter; tests give an `httpx.MockTransport`."""
        transport = self.env.context.get("brbank_http_transport")
        if isinstance(transport, httpx.AsyncBaseTransport):
            return transport
        return None

    def _l10n_br_bank_run(self, operation, callbacks=None, record=True):
        """Call the bank through the adapter, inside a dedicated event loop."""
        self.ensure_one()
        if not self.active:
            raise UserError(_("The bank connection %s is archived.", self.name))
        # Flush first, so a callback committing apart sees the row locks.
        self.flush_recordset()
        outcome = {}
        adapter_class, config = self._l10n_br_bank_prepare_adapter(
            callbacks=callbacks, outcome=outcome
        )
        transport = self._l10n_br_bank_http_transport()

        async def call():
            kwargs = {}
            if transport is not None:
                kwargs["client"] = httpx.AsyncClient(transport=transport)
            adapter = adapter_class(config, **kwargs)
            try:
                result = operation(adapter)
                if inspect.isawaitable(result):
                    result = await result
                return result
            finally:
                await adapter.aclose()

        try:
            result = run_in_dedicated_loop(call)
        except ErroBrbank as error:
            self._l10n_br_bank_after_call(outcome)
            if record:
                self._l10n_br_bank_record_failure(error)
            raise
        except BaseException:
            self._l10n_br_bank_after_call(outcome)
            raise
        self._l10n_br_bank_after_call(outcome)
        if record:
            self._l10n_br_bank_record_success()
        return result

    # === REFRESH TOKEN === #

    def _l10n_br_bank_refresh_callback(self, outcome):
        """`ao_renovar_refresh_token` of the adapter: commit the new token at once."""
        self.ensure_one()
        registry = self.env.registry
        connection_id = self.id

        def renew(token):
            outcome["refresh_token"] = token
            # Stays if the save below raises: the caller then writes it.
            outcome["refresh_token_unsaved"] = "interrupted"
            outcome["refresh_token_unsaved"] = _save_refresh_token(
                registry, connection_id, token
            )

        return renew

    def _l10n_br_bank_after_call(self, outcome):
        """Apply in the calling transaction what the callbacks reported."""
        self.ensure_one()
        token = outcome.get("refresh_token")
        if not token:
            return
        reason = outcome.get("refresh_token_unsaved")
        if not reason:
            cr = self.env.cr
            renewed = cr.cache.setdefault(RENEWED_TOKENS, {})
            if not renewed:

                def forget():
                    cr.cache.pop(RENEWED_TOKENS, None)

                cr.postcommit.add(forget)
                cr.postrollback.add(forget)
            renewed[self.id] = token
            return
        _logger.warning(
            "bank connection %s: the renewed refresh token is saved in the "
            "current transaction only (%s); a rollback loses it",
            self.id,
            reason,
        )
        self.sudo().refresh_token = token

    # === STATE === #

    def _l10n_br_bank_write_apart(self, values):
        """Write `values` in a cursor of its own, falling back to this one."""
        self.ensure_one()
        columns = ", ".join(f"{name} = %s" for name in values)
        try:
            with self.env.registry.cursor() as cr:
                cr.execute(
                    "SET LOCAL lock_timeout = %s",
                    (f"{int(APART_LOCK_TIMEOUT_MS)}ms",),
                    log_exceptions=False,
                )
                cr.execute(
                    f"UPDATE l10n_br_bank_connection_connection SET {columns}, "  # noqa: S608
                    "write_date = now() AT TIME ZONE 'UTC' WHERE id = %s",
                    (*values.values(), self.id),
                    log_exceptions=False,
                )
                done = bool(cr.rowcount)
        except psycopg2.Error:
            done = False
        if done:
            # Keep this transaction in line without a second UPDATE.
            self.invalidate_recordset(list(values))
            return
        self.sudo().write(values)

    def _l10n_br_bank_record_success(self):
        self.ensure_one()
        values = {}
        if self.state != "connected":
            values["state"] = "connected"
        if self.last_error:
            values["last_error"] = False
        if values:
            self._l10n_br_bank_write_apart(values)

    def _l10n_br_bank_record_failure(self, error):
        """Remember a failed call: the error text, never its body."""
        self.ensure_one()
        values = {"last_error": f"{type(error).__name__}: {error}"[:500]}
        if "token" in str(error).lower() and not isinstance(error, Indisponivel):
            values["state"] = "needs_reconsent" if self.oauth_supported else "error"
        if all(self[name] == value for name, value in values.items()):
            return
        self._l10n_br_bank_write_apart(values)

    # === HOOKS FOR THE DOMAIN MODULES === #

    def _l10n_br_bank_sync_report(self, domain, ok, message=False):
        """Record the last synchronization of a domain."""
        self.ensure_one()
        state = {True: "ok", False: "error", "warning": "warning"}[ok]
        status = self.env["l10n_br_bank_connection.sync_status"].sudo()
        row = status.search(
            [("connection_id", "=", self.id), ("domain", "=", domain)], limit=1
        )
        values = {
            "last_date": fields.Datetime.now(),
            "state": state,
            "message": (message or "")[:500],
        }
        if row:
            row.write(values)
        else:
            status.create(dict(values, connection_id=self.id, domain=domain))
        return row

    def _l10n_br_bank_handle_webhook(self, body, headers):
        """Handle a webhook call; domain modules extend it with `super()`."""
        self.ensure_one()
        return {}

    def _l10n_br_bank_test_connection(self):
        """Check that the bank accepts the connection; domains extend it."""
        self.ensure_one()

        async def probe(adapter):
            transport = getattr(adapter, "_transporte", None)
            auth = getattr(transport, "_auth", None)
            if auth is None:
                return False
            await auth.cabecalhos(None, transport.client)
            return True

        got_token = self._l10n_br_bank_run(probe)
        return [
            _("Access token obtained.")
            if got_token
            else _("The adapter has no token step.")
        ]

    # === ACTIONS === #

    def action_test_connection(self):
        self.ensure_one()
        self.check_access("write")
        try:
            lines = self._l10n_br_bank_test_connection()
            kind = "success"
        except (ErroBrbank, UserError) as error:
            lines = [str(error)]
            kind = "danger"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.name,
                "message": "\n".join(lines),
                "type": kind,
                "sticky": kind == "danger",
            },
        }

    def action_rotate_webhook_token(self):
        """Issue a new webhook token: the old URL stops working at once."""
        self.ensure_one()
        self.check_access("write")
        self.sudo().webhook_token = secrets.token_urlsafe(32)

    def action_fill_settings_template(self):
        """Add to the JSON fields the keys the adapter needs, keeping values."""
        self.ensure_one()
        connection = self.sudo()
        adapter_class = connection._l10n_br_bank_adapter_class()
        if not adapter_class:
            raise UserError(_("Choose the bank adapter first."))
        public = connection._l10n_br_bank_load_json("extra_config")
        secret = connection._l10n_br_bank_load_json("secret_config")
        config_cls = bank_config.config_class(adapter_class)
        for key in bank_config.describe(config_cls):
            if key["generic"] or key["callable"]:
                continue
            target = secret if key["secret"] else public
            if key["name"] not in public and key["name"] not in secret:
                target[key["name"]] = bank_config.placeholder(key)
        connection.write(
            {
                "extra_config": json.dumps(public, indent=2, sort_keys=True),
                "secret_config": json.dumps(secret, indent=2, sort_keys=True),
            }
        )

    def action_oauth_connect(self):
        """Open the consent at the bank (authorization code flow)."""
        self.ensure_one()
        self.check_access("write")
        if not self.oauth_supported:
            raise UserError(
                _(
                    "The adapter %s does not use the authorization code flow.",
                    self.adapter,
                )
            )
        if not self.id:
            raise UserError(_("Save the connection first."))
        return {
            "type": "ir.actions.act_url",
            "url": f"{OAUTH_START_ROUTE}/{self.id}",
            "target": "self",
        }

    # === OAUTH (AUTHORIZATION CODE + PKCE) === #

    def _l10n_br_bank_oauth_functions(self):
        """`(url_autorizacao, trocar_codigo)` of the adapter module, or None."""
        adapter = self.adapter
        if not adapter or adapter not in registro.listar_adapters():
            return None
        adapter_class = self._l10n_br_bank_adapter_class()
        if adapter_class is None:
            return None
        try:
            module = importlib.import_module(adapter_class.__module__)
        except ImportError:  # pragma: no cover
            return None
        authorize = getattr(module, "url_autorizacao", None)
        exchange = getattr(module, "trocar_codigo", None)
        if callable(authorize) and callable(exchange):
            return authorize, exchange
        return None

    @api.model
    def _l10n_br_bank_oauth_redirect_uri(self):
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        )
        return base_url.rstrip("/") + OAUTH_CALLBACK_ROUTE

    def _l10n_br_bank_oauth_start(self):
        """Start the consent and return the authorization URL of the bank."""
        self.ensure_one()
        functions = self._l10n_br_bank_oauth_functions()
        if not functions:
            raise UserError(
                _(
                    "The adapter %s does not use the authorization code flow.",
                    self.adapter,
                )
            )
        authorize, _exchange = functions
        _adapter_class, config = self._l10n_br_bank_prepare_adapter(oauth=True)
        state = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        self.sudo().write(
            {
                "oauth_state": state,
                "oauth_verifier": verifier,
                "oauth_expires": fields.Datetime.now() + OAUTH_VALIDITY,
            }
        )
        return authorize(
            config,
            self._l10n_br_bank_oauth_redirect_uri(),
            state,
            _pkce_challenge(verifier),
            self.sudo().scopes or getattr(config, "escopos_dda", None),
        )

    def _l10n_br_bank_oauth_finish(self, code):
        """Exchange the code for tokens; the `state` is single use."""
        self.ensure_one()
        connection = self.sudo()
        verifier = connection.oauth_verifier
        connection.write(
            {"oauth_state": False, "oauth_verifier": False, "oauth_expires": False}
        )
        functions = connection._l10n_br_bank_oauth_functions()
        if not functions or not verifier:
            raise UserError(_("The consent was not started or already used."))
        _authorize, exchange = functions
        _adapter_class, config = connection._l10n_br_bank_prepare_adapter(oauth=True)
        redirect_uri = self._l10n_br_bank_oauth_redirect_uri()

        async def call():
            result = exchange(config, code, redirect_uri, verifier)
            if inspect.isawaitable(result):
                result = await result
            return result

        try:
            tokens = run_in_dedicated_loop(call)
        except ErroBrbank as error:
            connection.write({"last_error": f"{type(error).__name__}: {error}"[:500]})
            raise UserError(
                _("The bank refused the authorization code: %s", error)
            ) from error
        refresh = (tokens or {}).get("refresh_token")
        if not refresh:
            raise UserError(_("The bank did not return a refresh token."))
        connection.write(
            {"refresh_token": refresh, "state": "connected", "last_error": False}
        )
        return True
