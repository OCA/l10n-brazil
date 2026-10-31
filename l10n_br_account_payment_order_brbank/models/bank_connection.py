# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import inspect
import re

import httpx
from brbank import registro
from brbank.erros import AdapterNaoEncontrado, ErroBrbank
from brbank.pagamento import CapacidadePagamento

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_bank_connection.models.connection import (
    GENERIC_FIELDS,
    SECRET_GROUP,
    _normalize_cnpj,
)
from odoo.addons.l10n_br_bank_connection.utils import config as bank_config
from odoo.addons.l10n_br_bank_connection.utils.runner import run_in_dedicated_loop


def _digits(value):
    return re.sub(r"\D", "", value or "")


class BankConnection(models.Model):
    _inherit = "l10n_br_bank_connection.connection"

    brbank_payment_settings = fields.Text(
        string="Payment Settings",
        groups=SECRET_GROUP,
        help="JSON object with the settings of the payment API that the charge "
        "settings do not have.",
    )
    brbank_payment_secrets = fields.Text(
        string="Payment Secrets",
        groups=SECRET_GROUP,
        help="JSON object with the secrets of the payment API that the charge "
        "secrets do not have.",
    )
    brbank_payment_settings_help = fields.Text(
        string="Payment Keys", compute="_compute_brbank_payment_settings_help"
    )

    @api.depends("adapter")
    def _compute_brbank_payment_settings_help(self):
        for connection in self:
            connection.brbank_payment_settings_help = False
            if not connection._l10n_br_bank_payment_capabilities():
                continue
            adapter_class = connection._l10n_br_bank_payment_adapter_class()
            keys = {
                key["name"]: key
                for key in bank_config.describe(bank_config.config_class(adapter_class))
            }
            holder = connection._l10n_br_bank_payment_holder(
                keys, self.env["res.partner.bank"]
            )
            connection.brbank_payment_settings_help = "\n".join(
                "{name}: {kind}{required}{secret}".format(
                    name=key["name"],
                    kind=getattr(key["type"], "__name__", "json"),
                    required=" *" if key["required"] else "",
                    secret=" [secret]" if key["secret"] else "",
                )
                for key in keys.values()
                if not key["generic"]
                and not key["callable"]
                and key["name"] not in holder
            )

    @api.constrains("brbank_payment_settings", "brbank_payment_secrets")
    def _check_brbank_payment_settings(self):
        for connection in self.sudo():
            connection._l10n_br_bank_load_json("brbank_payment_settings")
            connection._l10n_br_bank_load_json("brbank_payment_secrets")

    def _l10n_br_bank_payment_adapter_class(self):
        self.ensure_one()
        try:
            return registro.obter_classe_pagamento(self.adapter)
        except AdapterNaoEncontrado as error:
            raise UserError(
                _("The bank adapter %s cannot send payments.", self.adapter)
            ) from error

    def _l10n_br_bank_payment_capabilities(self):
        """What the payment adapter declares, read from the class."""
        self.ensure_one()
        try:
            return registro.obter_classe_pagamento(self.adapter).capacidades_pagamento
        except AdapterNaoEncontrado:
            return CapacidadePagamento.NENHUMA

    def _l10n_br_bank_payment_holder(self, keys, bank_account):
        """Values the Odoo data already has: the holder and the debit account."""
        company = self.company_id
        document = _normalize_cnpj(self.cnpj)
        branch_digit = (bank_account.bra_number_dig or "").strip()
        holder = {
            "pagador_documento": document,
            "documento_pagador": document,
            "pagador_nome": company.legal_name or company.name,
            "agencia": _digits(bank_account.bra_number),
            "digito_conta": (bank_account.acc_number_dig or "").strip().upper(),
            "digito_agencia": int(branch_digit) if branch_digit.isdigit() else False,
            "poupanca": bank_account.transactional_acc_type == "saving",
        }
        # Optional at Inter, where it means another thing (account with digit).
        if keys.get("conta_corrente", {}).get("required"):
            holder["conta_corrente"] = _digits(bank_account.acc_number)
        return holder

    def _l10n_br_bank_payment_config(self, adapter_class, mode, bank_account=None):
        """Payment configuration, by the fields of the Config of each adapter: the
        connection credentials, the holder and debit account, the keys of the extra
        settings the adapter knows, the mode and the payment settings."""
        connection = self.sudo()
        config_cls = bank_config.config_class(adapter_class)
        keys = {key["name"]: key for key in bank_config.describe(config_cls)}
        holder = connection._l10n_br_bank_payment_holder(
            keys, bank_account or mode.fixed_journal_id.bank_account_id
        )
        generic = {
            "conta": f"odoo-connection-{connection.id}",
            "ambiente": "sandbox" if connection.environment == "test" else "producao",
            "cnpj_empresa": _normalize_cnpj(connection.cnpj),
            **holder,
        }
        for field_name, key in GENERIC_FIELDS.items():
            value = connection[field_name]
            if value and connection._fields[field_name].type == "binary":
                value = base64.b64decode(value)
            generic[key] = value

        def known(values, secret=False):
            return {
                k: v
                for k, v in values.items()
                if k in keys
                and k not in holder
                and keys[k]["secret"] == secret
                and v not in (None, "")
            }

        public = known(connection._l10n_br_bank_load_json("extra_config"))
        public.update(
            known(
                {
                    "contrato": mode.brbank_contract,
                    "tipo_pagamento": int(mode.brbank_payment_kind or 126),
                    "finalidade_ted": mode.brbank_ted_purpose or None,
                }
            )
        )
        ted_purpose = keys.get("ted_finalidade", {})
        if ted_purpose.get("type") is int and mode.brbank_ted_purpose:
            public["ted_finalidade"] = mode.brbank_ted_purpose
        public.update(connection._l10n_br_bank_load_json("brbank_payment_settings"))
        secret = known(connection._l10n_br_bank_load_json("secret_config"), secret=True)
        secret.update(connection._l10n_br_bank_load_json("brbank_payment_secrets"))
        try:
            return bank_config.build(config_cls, generic, public, secret)
        except bank_config.ConfigError as error:
            details = ", ".join(error.missing + error.unknown + error.misplaced)
        except ErroBrbank as error:
            details = str(error)
        raise UserError(
            _(
                "Incomplete payment configuration of the connection %(name)s: "
                "%(details)s",
                name=connection.name,
                details=details,
            )
        )

    def _l10n_br_bank_record_payment_call(self, error=False):
        """Keep the last error of a payment call. The state of the connection
        follows the charge configuration, which a payment connection may lack."""
        self.ensure_one()
        message = error and f"{type(error).__name__}: {error}"[:500]
        if (self.last_error or False) != message:
            self._l10n_br_bank_write_apart({"last_error": message})

    def _l10n_br_bank_payment_run(self, mode, operation, bank_account=None):
        """Call the payment adapter of the connection in a dedicated event loop."""
        self.ensure_one()
        if not self.active:
            raise UserError(_("The bank connection %s is archived.", self.name))
        adapter_class = self._l10n_br_bank_payment_adapter_class()
        config = self._l10n_br_bank_payment_config(adapter_class, mode, bank_account)
        transport = self._l10n_br_bank_http_transport()
        refused = []

        async def call():
            kwargs = {}
            if transport is not None:
                kwargs["client"] = httpx.AsyncClient(transport=transport)
            try:
                adapter = adapter_class(config, **kwargs)
            except ErroBrbank as error:
                refused.append(error)
                return None
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
            self._l10n_br_bank_record_payment_call(error)
            raise
        if refused:
            raise UserError(
                _(
                    "Incomplete payment configuration of the connection %(name)s: "
                    "%(details)s",
                    name=self.name,
                    details=refused[0],
                )
            )
        self._l10n_br_bank_record_payment_call()
        return result
