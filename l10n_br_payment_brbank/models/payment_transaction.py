# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import json
import logging
import re
from decimal import Decimal

from brbank import Encargos, Endereco, Pessoa, StatusCanonico, Titulo, TituloRegistrado
from brbank.erros import Duplicado, ErroBrbank, Indisponivel
from pydantic import ValidationError as PydanticValidationError

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round, format_date

from .boleto_instruction import COMMANDS
from .payment_provider import BRBANK, NOSSO_NUMERO_CONTEXT

_logger = logging.getLogger(__name__)

# canonical status of the bank -> state of the transaction.
STATUS_TO_STATE = {
    StatusCanonico.PENDENTE_REGISTRO: "pending",
    StatusCanonico.REGISTRADO: "authorized",
    StatusCanonico.LIQUIDADO: "done",
    StatusCanonico.BAIXADO: "cancel",
    StatusCanonico.REJEITADO: "error",
}
# Source states each target accepts; a `done` transaction never goes back.
ALLOWED_SOURCES = {
    "pending": ("draft",),
    "authorized": ("draft", "pending"),
    "done": ("draft", "pending", "authorized", "error"),
    "cancel": ("draft", "pending", "authorized"),
    "error": ("draft", "pending", "authorized"),
}
REGISTERED_FIELDS = (
    ("nosso_numero", "our_number"),
    ("linha_digitavel", "digitable_line"),
    ("codigo_barras", "barcode"),
    ("pix_copia_cola", "pix_copia_cola"),
    ("txid", "txid"),
)
TECHNICAL_INFO_LIMIT = 4000
# Santander shows a boleto paid by Pix as written off, and brbank recognizes the
# payment by a text its guide does not define. Until a real Pix confirms that
# text, a write-off not commanded from Odoo goes to review instead of canceling.
WRITE_OFF_REVIEW_ADAPTERS = {"santander"}


def _agency_code(account):
    """Branch and account as printed on the boleto: 1607 / 99738672-X."""
    branch = account.bra_number or ""
    if account.bra_number_dig:
        branch = f"{branch}-{account.bra_number_dig}"
    number = account.acc_number or ""
    if account.acc_number_dig:
        number = f"{number}-{account.acc_number_dig}"
    return f"{branch} / {number}".strip(" /")


def _percent(value):
    """Odoo keeps 2% as 0.02 (percentage widget); the library wants 2."""
    if not value:
        return None
    return Decimal(str(float_round(value * 100, precision_digits=4)))


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    brbank_idempotency_key = fields.Char(
        string="Idempotency Key",
        readonly=True,
        copy=False,
        index=True,
        help="Key sent to the bank with the registration: repeating the call "
        "with the same key never creates a second title.",
    )
    brbank_seu_numero = fields.Char(
        string="Our Reference at the Bank", readonly=True, copy=False
    )
    brbank_nosso_numero = fields.Char(
        string="Nosso Numero Sent",
        readonly=True,
        copy=False,
        help="Taken from the sequence of the provider before the first "
        "registration call and sent again on every retry of this title.",
    )
    brbank_bank_status = fields.Char(string="Bank Status", readonly=True, copy=False)
    brbank_paid_amount = fields.Monetary(
        string="Amount Paid at the Bank",
        currency_field="currency_id",
        readonly=True,
        copy=False,
    )
    brbank_paid_date = fields.Date(string="Payment Date", readonly=True, copy=False)
    brbank_last_check = fields.Datetime(
        string="Last Bank Check", readonly=True, copy=False
    )
    brbank_review_message = fields.Char(
        string="Review Needed", readonly=True, copy=False
    )
    brbank_waive_fees = fields.Boolean(
        string="Fees Waived",
        readonly=True,
        copy=False,
        help="Issued without fine and interest: the bank charges only the amount, "
        "even after the due date.",
    )
    brbank_instruction_ids = fields.One2many(
        comodel_name="l10n_br.boleto.instruction",
        inverse_name="transaction_id",
        string="Bank Instructions",
    )
    brbank_boleto_action_available = fields.Boolean(
        compute="_compute_brbank_boleto_action_available"
    )
    brbank_supports_pdf = fields.Boolean(related="provider_id.brbank_supports_pdf")
    brbank_supports_instruction = fields.Boolean(
        related="provider_id.brbank_supports_instruction"
    )
    brbank_supports_write_off = fields.Boolean(
        related="provider_id.brbank_supports_write_off"
    )

    _sql_constraints = [
        (
            "brbank_idempotency_key_unique",
            "unique(brbank_idempotency_key)",
            "The idempotency key of a bank title must be unique.",
        )
    ]

    def _compute_brbank_boleto_action_available(self):
        Action = self.env["l10n_br.boleto.action"]
        for tx in self:
            tx.brbank_boleto_action_available = bool(
                tx.provider_code == BRBANK
                and tx._origin
                and Action._available_actions(tx._origin.sudo(), tx.move_line_id)
            )

    # === BUSINESS METHODS: TITLE === #

    def _brbank_new_idempotency_key(self, suffix):
        dbuuid = self.env["ir.config_parameter"].sudo().get_param("database.uuid")
        return f"odoo-{(dbuuid or '')[:8]}-{suffix}"

    def _brbank_partner(self):
        self.ensure_one()
        partner = self.invoice_ids[:1].partner_id or self.partner_id
        return partner.commercial_partner_id

    def _brbank_prepare_payer(self):
        """The payer of the title; the error names the missing fields only."""
        self.ensure_one()
        partner = self._brbank_partner()
        document = re.sub(r"[^0-9A-Za-z]", "", partner.vat or "")
        street = partner.street_name or partner.street
        city = partner.city_id.name or partner.city
        zip_code = re.sub(r"\D", "", partner.zip or "")
        missing = [
            label
            for label, value in (
                (_("CPF/CNPJ"), document),
                (_("Street"), street),
                (_("ZIP code"), len(zip_code) == 8),
                (_("City"), city),
                (_("State"), partner.state_id.code),
            )
            if not value
        ]
        if missing:
            raise UserError(
                _(
                    "The customer of the transaction %(ref)s is missing data the "
                    "bank requires: %(fields)s.",
                    ref=self.reference,
                    fields=", ".join(missing),
                )
            )
        return self._brbank_person(partner)

    @api.model
    def _brbank_person(self, partner):
        """`brbank.Pessoa` of a partner; the address only when it is complete."""
        street = partner.street_name or partner.street
        city = partner.city_id.name or partner.city
        zip_code = re.sub(r"\D", "", partner.zip or "")
        address = None
        if street and city and partner.state_id.code and len(zip_code) == 8:
            address = Endereco(
                logradouro=street,
                numero=partner.street_number or "SN",
                complemento=partner.street2 or "",
                bairro=partner.district or "",
                cidade=city,
                uf=partner.state_id.code,
                cep=zip_code,
            )
        return Pessoa(
            nome=partner.legal_name or partner.name,
            documento=re.sub(r"[^0-9A-Za-z]", "", partner.vat or ""),
            endereco=address,
            email=partner.email or None,
        )

    def _brbank_prepare_titulo(self):
        """Build the canonical title (`brbank.Titulo`); money goes as text."""
        self.ensure_one()
        mode = self.invoice_ids[:1].payment_mode_id
        due_date = self.due_date or self.move_line_id.date_maturity
        if not due_date:
            raise UserError(
                _("The transaction %s has no due date for the boleto.", self.reference)
            )
        messages = tuple(
            line.strip()
            for line in (self.boleto_instructions or "").splitlines()
            if line.strip()
        )
        if self.brbank_waive_fees:
            fees = Encargos()
        else:
            fees = Encargos(
                multa_percentual=_percent(
                    self.boleto_penalty or mode.payment_boleto_penalty
                ),
                juros_mensal_percentual=_percent(
                    self.boleto_interest or mode.payment_boleto_interest
                ),
            )
        try:
            return Titulo(
                chave_idempotencia=self.brbank_idempotency_key,
                seu_numero=self.brbank_seu_numero or str(self.id),
                valor=Decimal(f"{self.currency_id.round(self.amount):.2f}"),
                vencimento=due_date,
                pagador=self._brbank_prepare_payer(),
                encargos=fees,
                mensagens=messages,
            )
        except PydanticValidationError as error:
            # The pydantic message quotes the input: keep only the field names.
            names = sorted(
                {".".join(str(part) for part in item["loc"]) for item in error.errors()}
            )
            raise UserError(
                _(
                    "The bank title of the transaction %(ref)s has invalid data: "
                    "%(fields)s.",
                    ref=self.reference,
                    fields=", ".join(names),
                )
            ) from None

    def _brbank_register(self, raise_on_error=True):
        """Register the title at the bank, once; `Duplicado` reads it back."""
        self.ensure_one()
        if self.provider_code != BRBANK or self.provider_reference:
            return bool(self.provider_reference)
        if not self.brbank_idempotency_key:
            self.brbank_idempotency_key = self._brbank_new_idempotency_key(
                f"tx{self.id}"
            )
        try:
            self._brbank_check_due_date()
            self._brbank_reserve_nosso_numero()
            titulo = self._brbank_prepare_titulo()
        except UserError as error:
            if raise_on_error:
                raise
            self._set_error(error.args[0])
            return False
        provider = self.provider_id.sudo()
        if self.brbank_nosso_numero:
            provider = provider.with_context(
                **{
                    NOSSO_NUMERO_CONTEXT: {
                        titulo.chave_idempotencia: self.brbank_nosso_numero
                    }
                }
            )
        try:
            try:
                registered = provider._brbank_run(
                    lambda adapter: adapter.registrar_titulo(titulo)
                )
            except Duplicado as error:
                if not error.id_banco:
                    raise
                bank_id = error.id_banco
                registered = provider._brbank_run(
                    lambda adapter: adapter.consultar_titulo(bank_id)
                )
        except Indisponivel as error:
            _logger.info(
                "brbank: bank unavailable registering %s, will retry", self.reference
            )
            self.state_message = _(
                "The bank is unavailable, the registration will be retried: %s",
                error,
            )
            return False
        except ErroBrbank as error:
            message = _(
                "The bank refused the boleto of the transaction %(ref)s: %(error)s",
                ref=self.reference,
                error=error,
            )
            if raise_on_error:
                raise UserError(message) from None
            self._set_error(message)
            return False
        self._brbank_apply_registered(registered)
        return True

    def _brbank_check_due_date(self):
        """Banks refuse a title already past due (the BB answers HTTP 500), and
        a retry would never pass: refuse it here, with the way out."""
        self.ensure_one()
        if self._boleto_is_overdue():
            raise UserError(
                _(
                    "The due date of the boleto %(ref)s (%(date)s) has passed and "
                    "the bank does not register an overdue boleto. Change the due "
                    "date of the installment, or issue a new boleto from the "
                    "Boleto actions of the installment.",
                    ref=self.reference,
                    date=format_date(self.env, self.due_date),
                )
            )

    def _brbank_reserve_nosso_numero(self):
        """Keep the nosso numero on the transaction, so a retry sends the same one."""
        self.ensure_one()
        if self.brbank_nosso_numero:
            return self.brbank_nosso_numero
        number = self.provider_id.sudo()._brbank_next_nosso_numero()
        if number:
            self.brbank_nosso_numero = number
        return number

    def _brbank_fetch_pdf(self, raise_reason=False):
        """The boleto PDF: the bank's when it provides one, else drawn by brbank.

        Not fatal by default: without it the invoice still prints the digitable line
        and the Pix. A user asking for the PDF gets the reason (`raise_reason`).
        """
        self.ensure_one()
        if not self.brbank_supports_pdf:
            return self._brbank_render_pdf(raise_reason=raise_reason)
        reference = self.provider_reference
        try:
            pdf = self.provider_id.sudo()._brbank_run(
                lambda adapter: adapter.obter_pdf(reference)
            )
        except ErroBrbank as error:
            _logger.info(
                "brbank: no PDF for %s (%s)", self.reference, type(error).__name__
            )
            return False
        self.boleto_pdf = base64.b64encode(pdf)
        return True

    def _brbank_render_pdf(self, raise_reason=False):
        """Draw the boleto (payer receipt and compensation slip) with brbank.pdf."""
        self.ensure_one()
        if not (self.barcode or self.digitable_line):
            return False
        try:
            from brbank.pdf import BoletoPdf, Carteira, ConfigBoleto, gerar_boleto_pdf
        except ImportError:
            _logger.info("brbank: the boleto PDF needs brbank[pdf] (fpdf2, qrcode)")
            return False
        provider = self.provider_id.sudo()
        account = provider.journal_id.bank_account_id
        settings = provider.brbank_connection_id._l10n_br_bank_load_json("extra_config")
        company = self.company_id
        try:
            boleto = BoletoPdf(
                titulo=self._brbank_prepare_titulo(),
                registrado=TituloRegistrado(
                    banco=provider.brbank_adapter,
                    id_banco=self.provider_reference or self.reference,
                    status=StatusCanonico.REGISTRADO,
                    nosso_numero=self.our_number or None,
                    linha_digitavel=self.digitable_line or None,
                    codigo_barras=self.barcode or None,
                    pix_copia_cola=self.pix_copia_cola or None,
                ),
                carteira=Carteira(
                    banco=account.bank_id.code_bc or "",
                    agencia_codigo=_agency_code(account),
                    carteira=str(settings.get("carteira") or ""),
                    especie_documento=settings.get("especie") or "DM",
                ),
                beneficiario=self._brbank_person(company.partner_id),
            )
            logo = io.BytesIO(base64.b64decode(company.logo)) if company.logo else None
            pdf = gerar_boleto_pdf([boleto], ConfigBoleto(logo=logo))
        except (ErroBrbank, UserError, ValueError) as error:
            _logger.info(
                "brbank: boleto PDF of %s not drawn: %s", self.reference, error
            )
            if raise_reason:
                raise UserError(
                    _(
                        "The boleto of %(ref)s cannot be printed: the bank data "
                        "does not form a valid boleto (%(error)s).",
                        ref=self.reference,
                        error=error,
                    )
                ) from None
            return False
        self.boleto_pdf = base64.b64encode(pdf)
        return True

    def _brbank_sync_from_bank(self):
        """Read the title back from the bank and apply its status."""
        self.ensure_one()
        if self.provider_code != BRBANK or not self.provider_reference:
            return False
        reference = self.provider_reference
        registered = self.provider_id.sudo()._brbank_run(
            lambda adapter: adapter.consultar_titulo(reference)
        )
        self._brbank_apply_registered(registered)
        return True

    def _brbank_apply_registered(self, registered):
        """Copy a `TituloRegistrado` of the bank to the transaction."""
        self.ensure_one()
        values = {
            "provider_reference": registered.id_banco,
            "brbank_bank_status": registered.status.value,
            "brbank_last_check": fields.Datetime.now(),
            "is_boleto_payment": True,
        }
        for attribute, field_name in REGISTERED_FIELDS:
            value = getattr(registered, attribute)
            if value:
                values[field_name] = value
        if registered.valor_pago is not None:
            values["brbank_paid_amount"] = float(registered.valor_pago)
        if registered.data_pagamento:
            values["brbank_paid_date"] = registered.data_pagamento
        if registered.resposta_bruta:
            # Masked by the library: no personal data, no secret.
            values["provider_technical_info"] = json.dumps(
                registered.resposta_bruta, default=str, sort_keys=True
            )[:TECHNICAL_INFO_LIMIT]
        self.write(values)
        self._brbank_apply_status(registered.status)

    def _brbank_apply_status(self, status):
        """Move the transaction to the state of a status read from the bank."""
        self.ensure_one()
        target = STATUS_TO_STATE[StatusCanonico(status)]
        if self.state == target or self.state not in ALLOWED_SOURCES[target]:
            return False
        if target == "cancel" and self._brbank_write_off_needs_review():
            self._brbank_request_write_off_review()
            return False
        self.brbank_review_message = False
        # As core's own buttons: an invoicing user reads no provider, and core
        # would sign its log with the customer, who may have no email.
        tx = self.sudo().with_context(payment_backend_action=True)
        if target == "pending":
            tx._set_pending()
        elif target == "authorized":
            tx._set_authorized()
            if not self.boleto_pdf:
                self._brbank_fetch_pdf()
        elif target == "done":
            paid = self.brbank_paid_amount
            if paid and self.currency_id.compare_amounts(paid, self.amount) > 0:
                # The payment carries what the bank credited; the excess stays open.
                self.amount = paid
            tx._set_done()
            tx._post_process()
        elif target == "cancel":
            tx._set_canceled(_("Written off at the bank."))
            self._brbank_post_written_off()
        else:
            tx._set_error(_("The bank rejected the boleto."))
        return True

    def _brbank_invoice(self):
        self.ensure_one()
        return self.move_line_id.move_id or self.invoice_ids[:1]

    def _brbank_ask_a_person(self, message, summary):
        """Post on the invoice and schedule an activity for who can act on it."""
        self.ensure_one()
        invoice = self._brbank_invoice()
        if not invoice:
            return
        user = invoice.invoice_user_id
        if not user.has_group("account.group_account_invoice"):
            user = self.env.user
        invoice.message_post(body=message)
        invoice.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=summary,
            note=message,
            user_id=user.id,
        )

    def _brbank_write_off_needs_review(self):
        self.ensure_one()
        return self.provider_id.sudo().brbank_adapter in WRITE_OFF_REVIEW_ADAPTERS and (
            not self.brbank_instruction_ids.filtered(
                lambda i: i.command == "baixa" and i.state == "done"
            )
        )

    def _brbank_request_write_off_review(self):
        self.ensure_one()
        if self.brbank_review_message:
            return
        self.brbank_review_message = _(
            "The bank reports the boleto %s as written off, and no write-off was "
            "sent from Odoo: it may have been paid by Pix. Check it at the bank.",
            self.reference,
        )
        self._brbank_ask_a_person(
            self.brbank_review_message, _("Boleto written off at the bank: review")
        )

    def _brbank_post_written_off(self):
        self.ensure_one()
        invoice = self._brbank_invoice()
        if invoice and not self.move_line_id.reconciled:
            invoice.message_post(
                body=_(
                    "The boleto %s was written off at the bank. The title remains "
                    "open: the customer still owes this amount.",
                    self.reference,
                )
            )

    def _brbank_available_commands(self):
        """Write-off needs `BAIXA`, the other commands `ALTERACAO`, narrowed to the
        instructions the adapter declares (`instrucoes`, from brbank 0.0.19 on):
        the BB and the Sicredi do not protest, the C6 only extends."""
        self.ensure_one()
        commands = []
        if self.brbank_supports_instruction:
            provider = self.provider_id.sudo()
            adapter_class = provider._brbank_adapter_class()
            declared = getattr(adapter_class, "instrucoes", None)
            if hasattr(adapter_class, "instrucoes_da_config"):
                # The product may narrow it (Bradesco with QR code: no protest),
                # read from the public settings only, never the secrets.
                connection = provider.brbank_connection_id
                settings = (
                    connection._l10n_br_bank_load_json("extra_config")
                    if connection
                    else {}
                )
                declared = adapter_class.instrucoes_da_config(settings)
            commands += [
                command
                for command in ("prorrogacao", "abatimento", "protesto")
                if declared is None or COMMANDS[command] in declared
            ]
        if self.brbank_supports_write_off:
            commands.append("baixa")
        return commands

    def _brbank_is_live(self):
        """Registered and open at the bank: the boleto can still be paid."""
        self.ensure_one()
        return bool(
            self.provider_code == BRBANK
            and self.provider_reference
            and self.state == "authorized"
        )

    def _brbank_pending_write_off(self):
        """The write-off queued for this boleto, not sent yet."""
        self.ensure_one()
        return self.brbank_instruction_ids.filtered(
            lambda i: i.command == "baixa" and i.state == "draft" and i.idempotency_key
        )

    def _brbank_queue_write_off(self, reason):
        """Take the boleto off the bank once the invoice no longer charges it.

        Sent after the commit, never inside the transaction that decided it: a
        rollback would leave the bank without its boleto and Odoo unaware of it.
        A title never registered is just canceled here.
        """
        instructions = self.env["l10n_br.boleto.instruction"]
        for tx in self.filtered(lambda t: t.provider_code == BRBANK):
            if tx.state == "draft" and not tx.provider_reference:
                tx.sudo().with_context(payment_backend_action=True)._set_canceled(
                    reason
                )
                continue
            if (
                not tx._brbank_is_live()
                or not tx.brbank_supports_write_off
                or tx._brbank_pending_write_off()
            ):
                continue
            instruction = instructions.sudo().create(
                {"transaction_id": tx.id, "command": "baixa", "result_message": reason}
            )
            instruction.idempotency_key = tx._brbank_new_idempotency_key(
                f"instr{instruction.id}"
            )
            instructions |= instruction
        instructions._send_after_commit()
        return instructions

    # === CRON === #

    def _cron_brbank_reconcile(self, limit=200):
        """Safety net for the webhooks: retry registrations, read back open titles."""
        drafts = self.search(
            [
                ("provider_code", "=", BRBANK),
                ("provider_id.state", "!=", "disabled"),
                ("state", "=", "draft"),
                ("provider_reference", "=", False),
                ("brbank_idempotency_key", "!=", False),
            ],
            limit=limit,
        )
        results = {}
        for tx in drafts:
            error = tx._brbank_cron_step(
                lambda t: t._brbank_register(raise_on_error=False)
            )
            tx._brbank_count_sync(results, error)
        open_txs = self.search(
            [
                ("provider_code", "=", BRBANK),
                ("provider_id.state", "!=", "disabled"),
                ("state", "in", ("pending", "authorized")),
                ("provider_reference", "!=", False),
            ],
            order="brbank_last_check, id",
            limit=limit,
        )
        for tx in open_txs:
            error = tx._brbank_cron_step(lambda t: t._brbank_sync_from_bank())
            tx._brbank_count_sync(results, error)
        self._brbank_report_sync(results)
        # Instructions queued (automatic write-offs) or left by an unavailable bank.
        self.env["l10n_br.boleto.instruction"].search(
            [("state", "=", "draft"), ("idempotency_key", "!=", False)],
            limit=limit,
        )._send_queued()

    def _brbank_cron_step(self, step):
        """Run one step of the cron; return the error, if any."""
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                step(self)
        except (ErroBrbank, UserError) as error:
            _logger.info(
                "brbank: %s skipped by the reconciliation cron (%s)",
                self.reference,
                type(error).__name__,
            )
            if not isinstance(error, Indisponivel):
                self.brbank_last_check = fields.Datetime.now()
            return error
        return None

    def _brbank_count_sync(self, results, error):
        """Count the title of this cron round under its bank connection."""
        self.ensure_one()
        connection = self.provider_id.sudo().brbank_connection_id
        if not connection:
            return
        result = results.setdefault(connection.id, {"done": 0, "errors": []})
        result["done"] += 1
        if error is not None:
            result["errors"].append(error)

    @api.model
    def _brbank_report_sync(self, results):
        """Fill the Synchronization tab of every enabled brbank connection."""
        providers = (
            self.env["payment.provider"]
            .sudo()
            .search([("code", "=", BRBANK), ("state", "!=", "disabled")])
        )
        for connection in providers.mapped("brbank_connection_id"):
            result = results.get(connection.id, {"done": 0, "errors": []})
            errors = result["errors"]
            if not errors:
                connection._l10n_br_bank_sync_report(
                    "collection",
                    True,
                    _("%s titles checked at the bank.", result["done"]),
                )
                continue
            # Only "unavailable" errors clear by themselves on the next round.
            unavailable = all(isinstance(e, Indisponivel) for e in errors)
            last = errors[-1]
            connection._l10n_br_bank_sync_report(
                "collection",
                "warning" if unavailable else False,
                _(
                    "%(failed)s of %(total)s titles failed. Last error: %(error)s",
                    failed=len(errors),
                    total=result["done"],
                    error=last.args[0] if last.args else last,
                ),
            )

    # === BUSINESS METHODS: CNAB BRIDGE (O10) === #

    def _brbank_find_by_our_number(self, our_number, company=None):
        """The live brbank transaction of a nosso numero, for return files."""
        domain = [
            ("provider_code", "=", BRBANK),
            ("state", "in", ("pending", "authorized")),
            "|",
            ("our_number", "=", our_number),
            ("provider_reference", "=", our_number),
        ]
        if company:
            domain.append(("company_id", "=", company.id))
        return self.search(domain, limit=1)

    def _brbank_notify_cnab_occurrence(self, our_number, company=None):
        """Read the title back when a CNAB return reports it."""
        tx = self._brbank_find_by_our_number(our_number, company=company)
        if tx:
            tx._brbank_sync_from_bank()
        return tx

    # === PAYMENT FLOW === #

    def _send_capture_request(self, amount_to_capture=None):
        """ "Capture" reads the title back from the bank."""
        res = super()._send_capture_request(amount_to_capture=amount_to_capture)
        if self.provider_code == BRBANK:
            self.action_brbank_check_status()
        return res

    def _send_void_request(self, amount_to_void=None):
        """ "Void" writes the title off at the bank."""
        res = super()._send_void_request(amount_to_void=amount_to_void)
        if self.provider_code == BRBANK:
            self.action_brbank_write_off()
        return res

    # === ACTIONS === #

    def _brbank_raise_user_error(self, error):
        raise UserError(
            _(
                "The bank could not handle the request for %(ref)s: %(error)s",
                ref=self.reference,
                error=error,
            )
        ) from None

    def action_brbank_register(self):
        for tx in self:
            tx._brbank_register()

    def action_brbank_check_status(self):
        for tx in self:
            try:
                tx._brbank_sync_from_bank()
            except ErroBrbank as error:
                tx._brbank_raise_user_error(error)

    def action_brbank_download_pdf(self):
        self.ensure_one()
        if not self.boleto_pdf and not (
            self.provider_reference and self._brbank_fetch_pdf(raise_reason=True)
        ):
            raise UserError(_("The boleto PDF is not available yet."))
        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/payment.transaction/{self.id}/boleto_pdf/"
                f"boleto-{self.id}.pdf?download=true"
            ),
            "target": "new",
        }

    def action_brbank_boleto_actions(self):
        self.ensure_one()
        return self.env["l10n_br.boleto.action"]._open_for(self, self.move_line_id)

    def action_brbank_write_off(self):
        self.ensure_one()
        instruction = self.env["l10n_br.boleto.instruction"].create(
            {"transaction_id": self.id, "command": "baixa"}
        )
        return instruction.action_send()
