# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date

_logger = logging.getLogger(__name__)


class BoletoAction(models.TransientModel):
    """One step: choose what to do with the boleto of an installment, fill only
    what that action needs, send it. The answer stays on the transaction, in its
    Bank Instructions."""

    _name = "l10n_br.boleto.action"
    _description = "Boleto Actions"

    transaction_id = fields.Many2one(
        comodel_name="payment.transaction", string="Boleto", readonly=True
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line", string="Installment", readonly=True
    )
    currency_id = fields.Many2one(comodel_name="res.currency", readonly=True)
    current_due_date = fields.Date(string="Due Date", readonly=True)
    current_amount = fields.Monetary(
        string="Boleto Amount", currency_field="currency_id", readonly=True
    )
    open_amount = fields.Monetary(currency_field="currency_id", readonly=True)
    boleto_state = fields.Char(string="Boleto Status", readonly=True)
    available_type_ids = fields.Many2many(
        comodel_name="l10n_br.boleto.action.type",
        string="Available Actions",
        readonly=True,
    )
    action_type_id = fields.Many2one(
        comodel_name="l10n_br.boleto.action.type",
        string="What to do",
        required=True,
        domain="[('id', 'in', available_type_ids)]",
    )
    action = fields.Char(related="action_type_id.code")
    new_due_date = fields.Date()
    amount = fields.Monetary(string="Rebate Amount", currency_field="currency_id")
    charge_fees = fields.Boolean(
        string="Charge fine and interest after the new due date",
        default=True,
        help="Off: the new boleto charges only the open amount, even if paid late. "
        "Fine and interest of the old boleto are never carried over.",
    )
    explanation = fields.Text(compute="_compute_explanation")

    # === OPENING === #

    @api.model
    def _available_actions(self, transaction, installment):
        """What can be done now: the instructions the bank accepts on a live
        boleto; a new boleto when the current one can leave the bank."""
        actions = []
        if transaction and transaction._brbank_is_live():
            actions += transaction._brbank_available_commands()
            replaceable = "baixa" in actions
        else:
            replaceable = (
                not transaction
                or transaction.state
                in (
                    "cancel",
                    "error",
                )
                or (transaction.state == "draft" and not transaction.provider_reference)
            )
        if (
            installment
            and replaceable
            # An older boleto of the installment never issues a second one.
            and installment._brbank_boleto_transaction() == transaction
            and installment._brbank_can_issue_boleto()
        ):
            actions.append("reemissao")
        return actions

    @api.model
    def _open_for(self, transaction, installment):
        actions = self._available_actions(transaction, installment)
        if not actions:
            raise UserError(_("There is nothing to do with this boleto now."))
        reference = transaction or installment
        currency = transaction.currency_id or installment.currency_id
        types = self.env["l10n_br.boleto.action.type"].search([("code", "in", actions)])
        wizard = self.create(
            {
                "transaction_id": transaction.id,
                "move_line_id": installment.id,
                "currency_id": currency.id,
                "current_due_date": transaction.due_date or installment.date_maturity,
                "current_amount": transaction.amount,
                "open_amount": abs(installment.amount_residual_currency)
                if installment
                else transaction.amount,
                "boleto_state": dict(
                    transaction._fields["state"]._description_selection(self.env)
                ).get(transaction.state, "")
                if transaction
                else "",
                "available_type_ids": [Command.set(types.ids)],
                "action_type_id": types[:1].id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Boleto Actions: %s", reference.display_name),
            "res_model": self._name,
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.depends("action", "charge_fees", "transaction_id", "move_line_id")
    def _compute_explanation(self):
        texts = {
            "prorrogacao": _(
                "The bank moves the due date of this boleto. The installment of "
                "the invoice moves with it; the customer pays the same boleto."
            ),
            "abatimento": _(
                "The bank lowers the amount of this boleto. Odoo posts a credit "
                "note of the rebate, reconciled with the installment."
            ),
            "protesto": _(
                "The bank sends the boleto to a notary for protest. Use it only "
                "on an overdue boleto, as agreed with the bank."
            ),
            "baixa": _(
                "The bank cancels this boleto: it can no longer be paid. The "
                "installment stays open, the customer still owes it."
            ),
        }
        for wizard in self:
            if wizard.action == "reemissao":
                text = _(
                    "Odoo writes off the current boleto at the bank (when it is "
                    "still open there) and registers a new one for the open amount, "
                    "due on the new date. The installment moves to that date."
                )
                if not wizard.charge_fees:
                    text += " " + _("The new boleto carries no fine and no interest.")
                wizard.explanation = text
            else:
                wizard.explanation = texts.get(wizard.action, "")

    # === CONFIRMATION === #

    def action_confirm(self):
        self.ensure_one()
        actions = self._available_actions(self.transaction_id, self.move_line_id)
        if self.action not in actions:
            raise UserError(_("This action is no longer available for the boleto."))
        if self.action == "reemissao":
            result = self._reissue()
        else:
            result = self._send_instruction()
        return self._close_with(result)

    def _close_with(self, result):
        """Close the dialog and show the outcome; the form behind reloads."""
        if isinstance(result, dict) and result.get("tag") == "display_notification":
            result["params"]["next"] = {"type": "ir.actions.act_window_close"}
            return result
        return {"type": "ir.actions.act_window_close"}

    def _send_instruction(self):
        instruction = self.env["l10n_br.boleto.instruction"].create(
            {
                "transaction_id": self.transaction_id.id,
                "command": self.action,
                "new_due_date": self.new_due_date
                if self.action == "prorrogacao"
                else False,
                "amount": self.amount if self.action == "abatimento" else 0.0,
            }
        )
        result = instruction.action_send()
        if instruction.state == "done" and result is True:
            return instruction._notify(_("Accepted by the bank."), "success")
        return result

    def _today(self):
        transaction = self.transaction_id or self.env["payment.transaction"]
        tz = (
            self.move_line_id.partner_id.tz
            or transaction.company_id.partner_id.tz
            or self.env.company.partner_id.tz
            or "America/Sao_Paulo"
        )
        return fields.Date.context_today(self.with_context(tz=tz))

    def _reissue(self):
        """Write off the current boleto, then register a new one.

        The new title is built and checked before the write-off, so a missing
        customer data stops it with nothing done at the bank. Once the bank wrote
        the old boleto off, nothing here raises: a failure goes to a person.
        """
        installment = self.move_line_id
        old = self.transaction_id
        if not self.new_due_date or self.new_due_date < self._today():
            raise UserError(_("The new due date must be today or later."))
        invoice = installment.move_id
        installments = invoice.due_line_ids.sorted(
            lambda line: (line.date_maturity, line.id)
        )
        index = list(installments).index(installment) + 1
        values = invoice._brbank_prepare_transaction_values(installment, index)
        values["due_date"] = self.new_due_date
        if not self.charge_fees:
            values.update(
                {
                    "boleto_penalty": 0.0,
                    "boleto_interest": 0.0,
                    "brbank_waive_fees": True,
                }
            )
        new = self.env["payment.transaction"].sudo().create(values)
        new._brbank_prepare_titulo()

        if old and old._brbank_is_live():
            write_off = self.env["l10n_br.boleto.instruction"].create(
                {"transaction_id": old.id, "command": "baixa"}
            )
            write_off.action_send()
            if write_off.state != "done":
                new.unlink()
                if write_off.state == "draft":
                    # Bank unavailable (the BB refuses a write-off in the first 30
                    # minutes): the write-off belongs to this new boleto, so it must
                    # not be sent later by the queue.
                    write_off.state = "cancel"
                    return write_off._notify(
                        _(
                            "The bank cannot write off the boleto %(ref)s now, so "
                            "nothing was changed: %(error)s. Try again later.",
                            ref=old.reference,
                            error=write_off.result_message,
                        ),
                        "warning",
                    )
                return write_off._notify(
                    _(
                        "The bank did not write off the boleto %(ref)s, so no new "
                        "boleto was issued: %(error)s",
                        ref=old.reference,
                        error=write_off.result_message,
                    ),
                    "danger",
                )
        elif old and old.state == "draft":
            old.sudo().with_context(payment_backend_action=True)._set_canceled(
                _("Replaced by a new boleto.")
            )
        return self._register_new(new, old)

    def _register_new(self, new, old):
        installment = self.move_line_id
        old_date = installment.date_maturity
        try:
            with self.env.cr.savepoint():
                installment._brbank_set_due_date(self.new_due_date)
            registered = new._brbank_register(raise_on_error=False)
        except Exception as error:
            _logger.warning("brbank: new boleto %s not registered: %s", new.id, error)
            registered = False
            new.state_message = str(error)
        invoice = installment.move_id
        values = {
            "old": old.reference or _("none"),
            "new": new.reference,
            "old_date": format_date(self.env, old_date),
            "date": format_date(self.env, self.new_due_date),
            "fees": _("with fine and interest")
            if self.charge_fees
            else _("without fine and interest"),
        }
        if not registered and new.state == "draft":
            # Bank unavailable: the reconciliation cron registers it later.
            invoice.message_post(
                body=_(
                    "The boleto %(old)s left the bank. The bank is unavailable: the "
                    "new boleto %(new)s, due on %(date)s, will be registered by the "
                    "next retry.",
                    **values,
                )
            )
            return self.env["l10n_br.boleto.instruction"]._notify(
                _(
                    "The bank is unavailable: the new boleto %(new)s will be "
                    "registered by the next retry.",
                    **values,
                ),
                "warning",
            )
        if not registered:
            message = _(
                "The boleto %(old)s left the bank, but the new boleto %(new)s was not "
                "registered: %(error)s. Fix it and issue the boleto again from the "
                "installment.",
                old=values["old"],
                new=values["new"],
                error=new.state_message or "",
            )
            new.sudo()._brbank_ask_a_person(message, _("New boleto not registered"))
            return self.env["l10n_br.boleto.instruction"]._notify(message, "danger")
        invoice.message_post(
            body=_(
                "New boleto %(new)s issued in place of %(old)s: due date "
                "%(old_date)s -> %(date)s, %(fees)s.",
                **values,
            )
        )
        return self.env["l10n_br.boleto.instruction"]._notify(
            _("New boleto %(new)s registered at the bank, due on %(date)s.", **values),
            "success",
        )
