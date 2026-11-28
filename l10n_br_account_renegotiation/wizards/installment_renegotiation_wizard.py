# Copyright 2026 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class InstallmentRenegotiationWizard(models.TransientModel):
    _name = "account.installment.renegotiation.wizard"
    _description = "Installment Renegotiation Wizard"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
        required=True,
        readonly=True,
        ondelete="cascade",
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="move_id.currency_id",
        readonly=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="move_id.company_id",
        readonly=True,
    )

    original_total = fields.Monetary(
        compute="_compute_totals",
        currency_field="currency_id",
        help="Total amount of unreconciled installments before renegotiation",
    )

    new_total = fields.Monetary(
        compute="_compute_totals",
        currency_field="currency_id",
        help="Total amount of new installments",
    )

    difference = fields.Monetary(
        compute="_compute_totals",
        currency_field="currency_id",
        help="Difference between original and new totals (must be zero)",
    )

    line_ids = fields.One2many(
        comodel_name="account.installment.renegotiation.wizard.line",
        inverse_name="wizard_id",
        string="Installments",
    )

    payment_term_id = fields.Many2one(
        comodel_name="account.payment.term",
        string="New Payment Term",
        help="Select a payment term to automatically regenerate the installments.",
    )

    starting_date = fields.Date(
        help="Base date for computing the new payment term. "
        "Leave as the Invoice Date for corrections, "
        "or change to today's date for debt renegotiations.",
    )

    @api.onchange("payment_term_id", "starting_date")
    def _onchange_payment_term_id(self):
        """Regenerate the installment lines when a new payment term/date is selected."""
        if (
            not self.payment_term_id
            or not self.starting_date
            or not self.original_total
        ):
            return

        currency = self.currency_id
        company = self.company_id

        # Calculate amount in company currency in case of multi-currency
        if currency != company.currency_id:
            amount_company = currency._convert(
                self.original_total, company.currency_id, company, self.starting_date
            )
        else:
            amount_company = self.original_total

        # Leverage standard Odoo 18 payment term computation
        # We pass the full remaining total as the 'untaxed' amount
        # to simply split the balance
        pay_term = self.payment_term_id._compute_terms(
            date_ref=self.starting_date,
            currency=currency,
            tax_amount_currency=0.0,
            tax_amount=0.0,
            untaxed_amount_currency=self.original_total,
            untaxed_amount=amount_company,
            company=company,
            cash_rounding=self.move_id.invoice_cash_rounding_id,
            sign=1,  # Wizard lines always display positive amounts
        )

        # Clear existing lines and create the new ones based on the term computation
        commands = [Command.clear()]
        commands += [
            Command.create(
                {
                    "date_maturity": line.get("date"),
                    "amount": line.get("foreign_amount", 0.0),
                    "payment_mode_id": self.move_id.payment_mode_id.id
                    if "payment_mode_id" in self.move_id._fields
                    else False,
                }
            )
            for line in pay_term.get("line_ids", [])
        ]

        self.line_ids = commands

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-populate fields and installment lines."""
        for vals in vals_list:
            if "move_id" in vals:
                move = self.env["account.move"].browse(vals["move_id"])
                vals.setdefault("payment_term_id", move.invoice_payment_term_id.id)
                vals.setdefault(
                    "starting_date",
                    move.invoice_date or move.date or fields.Date.context_today(move),
                )

        wizards = super().create(vals_list)

        # Iterate to populate lines for each wizard created
        for wizard in wizards:
            wizard._populate_lines()

        return wizards

    def _populate_lines(self):
        """Populate wizard lines from the invoice's unreconciled payment_term lines."""
        self.ensure_one()

        # Get unreconciled payment_term lines
        payment_lines = self.move_id.line_ids.filtered(
            lambda line: line.display_type == "payment_term" and not line.reconciled
        )
        commands = [Command.clear()]
        for line in payment_lines:
            vals = {
                "original_line_id": line.id,
                "date_maturity": line.date_maturity,
                "amount": abs(line.amount_currency),
            }
            if "payment_mode_id" in line._fields:
                vals["payment_mode_id"] = line.payment_mode_id.id
            commands.append(Command.create(vals))
        self.line_ids = commands

    @api.depends("line_ids.amount")
    def _compute_totals(self):
        for wizard in self:
            # Calculate original total from unreconciled payment_term lines
            payment_lines = wizard.move_id.line_ids.filtered(
                lambda line: line.display_type == "payment_term" and not line.reconciled
            )
            wizard.original_total = sum(
                abs(line.amount_currency) for line in payment_lines
            )
            wizard.new_total = sum(wizard.line_ids.mapped("amount"))
            wizard.difference = wizard.new_total - wizard.original_total

    def _validate_renegotiation(self):
        """Validate that the renegotiation is valid before applying."""
        self.ensure_one()

        # Check user permission
        if not self.env.user.has_group("account.group_account_manager"):
            raise UserError(
                _(
                    "Only users with 'Billing Administrator' rights can "
                    "renegotiate installments."
                )
            )

        # Check move state
        if self.move_id.state != "posted":
            raise UserError(
                _("The invoice must be posted to renegotiate installments.")
            )

        # Check total hasn't changed
        precision = self.currency_id.rounding
        if float_compare(self.difference, 0, precision_rounding=precision) != 0:
            raise UserError(
                _(
                    "The total amount of installments must remain unchanged. "
                    "Current difference: %(diff)s",
                    diff=self.currency_id.format(self.difference),
                )
            )

        # Check at least one line
        if not self.line_ids:
            raise UserError(_("You must have at least one installment."))

        # Check all amounts are positive
        if any(line.amount <= 0 for line in self.line_ids):
            raise UserError(_("All installment amounts must be greater than zero."))

        # Check all dates are filled
        if any(not line.date_maturity for line in self.line_ids):
            raise UserError(_("All installments must have a due date."))

    def _renegotiation_kept_lines(self, original_lines):
        """Wizard lines left as they were: their installment stays untouched, and
        so do its boleto and CNAB remittance."""
        self.ensure_one()
        precision = self.currency_id.rounding
        kept = self.env["account.installment.renegotiation.wizard.line"]
        for wiz_line in self.line_ids:
            original = wiz_line.original_line_id
            if (
                original in original_lines
                and wiz_line.date_maturity == original.date_maturity
                and float_compare(
                    wiz_line.amount,
                    abs(original.amount_currency),
                    precision_rounding=precision,
                )
                == 0
                and (
                    "payment_mode_id" not in original._fields
                    or wiz_line.payment_mode_id == original.payment_mode_id
                )
            ):
                kept |= wiz_line
        return kept

    def _line_data(self, line):
        data = {
            "date_maturity": line.date_maturity,
            "amount_currency": line.amount_currency,
        }
        if "payment_mode_id" in line._fields and line.payment_mode_id:
            data["payment_mode"] = line.payment_mode_id.name
        return data

    def action_apply(self):
        """Apply the renegotiation to the invoice.

        The installments replaced are not deleted: they are zeroed and keep their
        original amount, so whatever points to them (a boleto transaction, a CNAB
        remittance line) keeps its history. Installments left unchanged in the
        wizard stay as they are.
        """
        self.ensure_one()
        self._validate_renegotiation()

        move = self.move_id
        original_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term" and not line.reconciled
        )
        kept = self._renegotiation_kept_lines(original_lines)
        replaced = original_lines - kept.mapped("original_line_id")
        if not replaced:
            raise UserError(_("Nothing to renegotiate: no installment was changed."))

        old_lines_data = [
            self._line_data(line) for line in replaced.sorted("date_maturity")
        ]
        move._installment_renegotiation_before(replaced)

        sign = 1 if move.is_inbound() else -1
        # Prepare context for bypassing readonly restrictions
        ctx = dict(
            self.env.context,
            skip_invoice_sync=True,
            allow_installment_renegotiation=True,
            check_move_validity=False,
            skip_readonly_check=True,
        )
        account_id = replaced[0].account_id.id

        if (
            self.payment_term_id
            and move.invoice_payment_term_id != self.payment_term_id
        ):
            move.with_context(**ctx).sudo().write(
                {"invoice_payment_term_id": self.payment_term_id.id}
            )

        for line in replaced:
            line.with_context(**ctx).sudo().write(
                {
                    "installment_original_amount": abs(line.amount_currency),
                    "amount_currency": 0.0,
                    "balance": 0.0,
                }
            )

        new_lines = self.env["account.move.line"]
        for wiz_line in (self.line_ids - kept).sorted("date_maturity"):
            amount_currency = sign * wiz_line.amount
            # For multi-currency, compute balance
            if move.currency_id != move.company_currency_id:
                balance = move.currency_id._convert(
                    amount_currency,
                    move.company_currency_id,
                    move.company_id,
                    move.date,
                )
            else:
                balance = amount_currency
            create_vals = {
                "move_id": move.id,
                "display_type": "payment_term",
                "name": "",
                "account_id": account_id,
                "date_maturity": wiz_line.date_maturity,
                "amount_currency": amount_currency,
                "balance": balance,
                "currency_id": move.currency_id.id,
                "partner_id": move.partner_id.id,
            }
            if wiz_line.payment_mode_id:
                create_vals["payment_mode_id"] = wiz_line.payment_mode_id.id
            new_lines |= (
                self.env["account.move.line"]
                .with_context(**ctx)
                .sudo()
                .create(create_vals)
            )

        move._installment_renegotiation_after(replaced, new_lines)

        new_lines_data = [
            self._line_data(line) for line in new_lines.sorted("date_maturity")
        ]
        message = move._get_installment_renegotiation_message(
            old_lines_data, new_lines_data
        )
        move.message_post(body=message)

        return {"type": "ir.actions.act_window_close"}


class InstallmentRenegotiationWizardLine(models.TransientModel):
    _name = "account.installment.renegotiation.wizard.line"
    _description = "Installment Renegotiation Wizard Line"
    _order = "date_maturity"

    wizard_id = fields.Many2one(
        comodel_name="account.installment.renegotiation.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )

    original_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Original Line",
        readonly=True,
        help="The original invoice line this installment is based on (if any)",
    )

    date_maturity = fields.Date(
        string="Due Date",
        required=True,
    )

    amount = fields.Monetary(
        required=True,
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="wizard_id.currency_id",
        readonly=True,
    )

    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        string="Payment Mode",
        domain="[('company_id', '=', company_id)]",
    )

    company_id = fields.Many2one(related="wizard_id.company_id")
