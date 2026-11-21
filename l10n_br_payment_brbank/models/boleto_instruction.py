# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from decimal import Decimal

from brbank import Instrucao, TipoInstrucao
from brbank.erros import Duplicado, ErroBrbank, Indisponivel, NaoSuportado, Validacao

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date
from odoo.tools.misc import format_amount

from .payment_provider import BRBANK, TXID_CONTEXT

_logger = logging.getLogger(__name__)

COMMANDS = {
    "prorrogacao": TipoInstrucao.PRORROGACAO,
    "abatimento": TipoInstrucao.ABATIMENTO,
    "protesto": TipoInstrucao.PROTESTO,
    "baixa": TipoInstrucao.BAIXA,
}


class BoletoInstruction(models.Model):
    """A command sent to the bank about a registered title, with its answer."""

    _name = "l10n_br.boleto.instruction"
    _description = "Boleto Bank Instruction"
    _order = "id desc"

    name = fields.Char(compute="_compute_name", store=True)
    transaction_id = fields.Many2one(
        comodel_name="payment.transaction",
        string="Transaction",
        required=True,
        ondelete="cascade",
        index=True,
        domain=[("provider_code", "=", BRBANK)],
    )
    provider_id = fields.Many2one(related="transaction_id.provider_id", store=True)
    company_id = fields.Many2one(related="transaction_id.company_id", store=True)
    currency_id = fields.Many2one(related="transaction_id.currency_id")
    command = fields.Selection(selection="_selection_command", required=True)
    new_due_date = fields.Date()
    amount = fields.Monetary(string="Rebate Amount", currency_field="currency_id")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Accepted"),
            ("rejected", "Rejected"),
            ("error", "Error"),
            ("cancel", "Not Needed"),
        ],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
    )
    idempotency_key = fields.Char(readonly=True, copy=False, index=True)
    result_message = fields.Char(string="Result", readonly=True, copy=False)
    bank_response = fields.Text(
        readonly=True,
        copy=False,
        groups="base.group_no_one",
        help="Answer of the bank, masked: no personal data, no secret.",
    )

    _sql_constraints = [
        (
            "idempotency_key_unique",
            "unique(idempotency_key)",
            "The idempotency key of a bank instruction must be unique.",
        )
    ]

    @api.model
    def _selection_command(self):
        return [
            ("prorrogacao", _("Due date extension")),
            ("abatimento", _("Rebate")),
            ("protesto", _("Protest")),
            ("baixa", _("Write-off")),
        ]

    @api.depends("transaction_id.reference", "command")
    def _compute_name(self):
        labels = dict(self._fields["command"]._description_selection(self.env))
        for instruction in self:
            instruction.name = "{} - {}".format(
                instruction.transaction_id.reference or "",
                labels.get(instruction.command, ""),
            )

    @api.constrains("command", "new_due_date", "amount")
    def _check_command_values(self):
        for instruction in self:
            if instruction.command == "prorrogacao" and not instruction.new_due_date:
                raise ValidationError(_("A due date extension needs the new date."))
            if instruction.command == "abatimento" and (
                instruction.currency_id.compare_amounts(instruction.amount, 0) <= 0
                or instruction.currency_id.compare_amounts(
                    instruction.amount, instruction.transaction_id.amount
                )
                >= 0
            ):
                raise ValidationError(
                    _("The rebate must be above zero and below the boleto amount.")
                )

    def _prepare_instrucao(self):
        self.ensure_one()
        return Instrucao(
            chave_idempotencia=self.idempotency_key,
            tipo=COMMANDS[self.command],
            nova_data_vencimento=self.new_due_date or None,
            valor=Decimal(f"{self.amount:.2f}") if self.amount else None,
        )

    def _check_can_send(self):
        """Refuse before the call: what the bank accepts cannot be undone here."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only a draft instruction can be sent."))
        transaction = self.transaction_id
        if (
            transaction.provider_code != BRBANK
            or not transaction.provider_reference
            or transaction.state != "authorized"
        ):
            raise UserError(_("The boleto is not registered at the bank."))
        if self.command not in transaction._brbank_available_commands():
            raise UserError(
                _("The bank of this provider does not accept this instruction.")
            )
        installment = transaction.move_line_id
        if self.command == "abatimento" and installment:
            provider = transaction.provider_id.sudo()
            if not provider.brbank_rebate_account_id:
                raise UserError(
                    _(
                        "Set the rebate account of the payment provider %s before "
                        "sending a rebate.",
                        provider.name,
                    )
                )
            residual = abs(installment.amount_residual_currency)
            if self.currency_id.compare_amounts(self.amount, residual) >= 0:
                raise UserError(
                    _("The rebate must be below the open amount of the installment.")
                )

    def action_send(self):
        """Send the instruction to the bank and record its answer."""
        self.ensure_one()
        self._check_can_send()
        transaction = self.transaction_id
        if not self.idempotency_key:
            self.idempotency_key = transaction._brbank_new_idempotency_key(
                f"instr{self.id}"
            )
        reference = transaction.provider_reference
        provider = transaction.provider_id.sudo().with_context(
            **{TXID_CONTEXT: {reference: transaction.txid}}
        )
        registered = None
        try:
            if self.command == "baixa":
                registered = provider._brbank_run(
                    lambda adapter: adapter.baixar_titulo(reference)
                )
            else:
                instrucao = self._prepare_instrucao()
                registered = provider._brbank_run(
                    lambda adapter: adapter.enviar_instrucao(reference, instrucao)
                )
        except Duplicado:
            # Accepted by an earlier call whose answer never reached Odoo.
            self.write(
                {
                    "state": "done",
                    "result_message": _("The bank had already applied it."),
                }
            )
        except Indisponivel as error:
            self.result_message = _(
                "Bank unavailable, Odoo sends it again by itself: %s", error
            )
            return self._notify(self.result_message, "warning")
        except (NaoSuportado, Validacao) as error:
            self._record_failure("rejected", error)
            return self._notify(self.result_message, "danger")
        except ErroBrbank as error:
            self._record_failure("error", error)
            return self._notify(self.result_message, "danger")
        else:
            self.write({"state": "done", "result_message": _("Accepted by the bank.")})
            self.sudo().bank_response = json.dumps(
                registered.resposta_bruta, default=str, sort_keys=True
            )
        return self._apply_acceptance(registered)

    def _apply_acceptance(self, registered):
        """The bank already did it: a local failure is reported, never raised."""
        self.ensure_one()
        transaction = self.transaction_id
        try:
            with self.env.cr.savepoint():
                if self.command == "prorrogacao":
                    transaction.due_date = self.new_due_date
                elif self.command == "abatimento":
                    transaction.amount -= self.amount
                if self.command in ("prorrogacao", "abatimento"):
                    # The stored PDF shows the old due date or amount: the next
                    # print fetches it from the bank or draws it again.
                    transaction.boleto_pdf = False
        except Exception as error:
            return self._report_local_failure(error)
        # Invoice effect first: a title answered as paid would close the installment
        # before the rebate credit note.
        invoice_error = None
        try:
            with self.env.cr.savepoint():
                self._apply_to_invoice()
        except Exception as error:
            invoice_error = error
        try:
            with self.env.cr.savepoint():
                if registered:
                    transaction._brbank_apply_registered(registered)
        except Exception as error:
            return self._report_local_failure(error)
        if invoice_error:
            return self._report_local_failure(invoice_error)
        if not registered:
            transaction._brbank_cron_step(lambda tx: tx._brbank_sync_from_bank())
        if self.command == "baixa" and transaction.state == "authorized":
            # Some banks (the BB) report the write-off only on the next day: the
            # boleto leaves the invoice and the portal now, as the bank accepted it.
            transaction.sudo().with_context(payment_backend_action=True)._set_canceled(
                _("Write-off accepted by the bank.")
            )
            transaction._brbank_post_written_off()
        return True

    def _apply_to_invoice(self):
        self.ensure_one()
        installment = self.transaction_id.move_line_id
        if not installment:
            return
        if self.command == "prorrogacao":
            self._apply_due_date(installment)
        elif self.command == "abatimento":
            self._post_rebate_credit_note(installment)

    def _apply_due_date(self, installment):
        old_date = installment.date_maturity
        installment._brbank_set_due_date(self.new_due_date)
        installment.move_id.message_post(
            body=_(
                "The bank accepted the new due date of the boleto %(ref)s: "
                "%(old)s -> %(new)s.",
                ref=self.transaction_id.reference,
                old=format_date(self.env, old_date),
                new=format_date(self.env, self.new_due_date),
            )
        )

    def _prepare_rebate_credit_note(self, installment):
        """A plain entry, not a reversal: no fiscal operation, no taxes, and core
        would reconcile a reversal with the oldest installment."""
        invoice = installment.move_id
        transaction = self.transaction_id
        reference = transaction.reference
        account = transaction.provider_id.sudo().brbank_rebate_account_id
        return {
            "move_type": "out_refund",
            "partner_id": invoice.partner_id.id,
            "journal_id": invoice.journal_id.id,
            "currency_id": invoice.currency_id.id,
            "invoice_date": fields.Date.context_today(self),
            "invoice_origin": invoice.name,
            "ref": _("Rebate of the boleto %s", reference),
            "fiscal_position_id": False,
            "invoice_payment_term_id": False,
            # A payment mode that issues boletos would charge the credit note.
            "payment_mode_id": False,
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": _("Rebate of the boleto %s", reference),
                        "account_id": account.id,
                        "quantity": 1,
                        "price_unit": self.amount,
                        "tax_ids": [Command.clear()],
                    }
                )
            ],
        }

    def _post_rebate_credit_note(self, installment):
        invoice = installment.move_id
        credit_note = (
            self.env["account.move"]
            .with_company(invoice.company_id)
            .create(self._prepare_rebate_credit_note(installment))
        )
        receivable = credit_note.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        receivable.account_id = installment.account_id
        credit_note.action_post()
        (receivable + installment).reconcile()
        invoice.message_post(
            body=_(
                "The bank accepted a rebate of %(amount)s on the boleto %(ref)s: "
                "credit note %(note)s.",
                amount=format_amount(self.env, self.amount, self.currency_id),
                ref=self.transaction_id.reference,
                note=credit_note.name,
            )
        )
        return credit_note

    def _report_local_failure(self, error):
        """Keep the record of the acceptance and ask a person to finish the job."""
        _logger.warning(
            "brbank: instruction %s accepted by the bank, not applied here: %s",
            self.id,
            error,
        )
        message = _(
            "The bank accepted the instruction %(name)s, but Odoo could not apply "
            "it to the invoice: %(error)s. Apply it by hand.",
            name=self.name,
            error=error,
        )
        self.result_message = message
        try:
            with self.env.cr.savepoint():
                self.transaction_id._brbank_ask_a_person(
                    message, _("Bank instruction not applied to the invoice")
                )
        except Exception as report_error:
            _logger.warning(
                "brbank: instruction %s not reported on the invoice: %s",
                self.id,
                report_error,
            )
        return self._notify(message, "danger")

    def _record_failure(self, state, error):
        self.write({"state": state, "result_message": str(error)})
        self.sudo().bank_response = json.dumps(
            getattr(error, "resposta_bruta", None), default=str
        )

    def _notify(self, message, kind):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"message": message, "type": kind, "sticky": False},
        }

    # === QUEUE === #

    def _send_after_commit(self):
        """Send the queued instructions once the decision that queued them is
        committed; the reconciliation cron sends what this misses."""
        if not self:
            return
        ids = self.ids
        uid = self.env.uid
        context = dict(self.env.context)
        registry = self.env.registry

        @self.env.cr.postcommit.add
        def send_queued():
            with registry.cursor() as cr:
                env = api.Environment(cr, uid, context)
                env[self._name].browse(ids).exists()._send_queued()

    def _send_queued(self):
        """Send each queued instruction, unless the boleto already left the bank."""
        for instruction in self.filtered(
            lambda i: i.state == "draft" and i.idempotency_key
        ):
            transaction = instruction.transaction_id
            if instruction.command == "baixa" and transaction._brbank_is_live():
                # Paid at the bank in the meantime? Then there is nothing to write off.
                error = transaction._brbank_cron_step(
                    lambda tx: tx._brbank_sync_from_bank()
                )
                if isinstance(error, Indisponivel):
                    continue
            if not transaction._brbank_is_live():
                instruction._cancel_not_needed()
                continue
            try:
                with self.env.cr.savepoint():
                    instruction.action_send()
            except (ErroBrbank, UserError) as error:
                _logger.info(
                    "brbank: queued instruction %s not sent (%s)",
                    instruction.id,
                    type(error).__name__,
                )
                instruction._record_failure("error", error)
            if instruction.command == "baixa" and instruction.state in (
                "rejected",
                "error",
            ):
                transaction._brbank_ask_a_person(
                    _(
                        "The bank did not write off the boleto %(ref)s (%(error)s): "
                        "it can still be paid. Write it off at the bank.",
                        ref=transaction.reference,
                        error=instruction.result_message,
                    ),
                    _("Boleto still open at the bank"),
                )

    def _cancel_not_needed(self):
        """The boleto left the bank before the instruction: record why, and ask a
        person when an invoice paid by other means was also paid at the bank."""
        self.ensure_one()
        transaction = self.transaction_id
        self.write(
            {
                "state": "cancel",
                "result_message": _("The boleto is no longer open at the bank."),
            }
        )
        installment = transaction.move_line_id
        if (
            self.command == "baixa"
            and transaction.state == "done"
            and installment.reconciled
            and transaction.payment_id
            not in installment.matched_credit_ids.credit_move_id.payment_id
        ):
            transaction._brbank_ask_a_person(
                _(
                    "The boleto %s was paid at the bank, and the installment had "
                    "already been paid by other means: the customer paid twice. "
                    "Refund the customer or keep the amount as a credit.",
                    transaction.reference,
                ),
                _("Installment paid twice"),
            )
