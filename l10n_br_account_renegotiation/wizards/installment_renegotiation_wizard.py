# Copyright 2026 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
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

    @api.model
    def create(self, vals):
        """Override create to auto-populate installment lines from the invoice."""
        wizard = super().create(vals)
        wizard._populate_lines()
        return wizard

    def _populate_lines(self):
        """Populate wizard lines from the invoice's unreconciled payment_term lines."""
        self.ensure_one()

        # Get unreconciled payment_term lines
        payment_lines = self.move_id.line_ids.filtered(
            lambda line: line.display_type == "payment_term" and not line.reconciled
        )

        line_vals = []
        for line in payment_lines:
            line_vals.append(
                (
                    0,
                    0,
                    {
                        "original_line_id": line.id,
                        "date_maturity": line.date_maturity,
                        "amount": abs(line.amount_currency),
                    },
                )
            )

        self.line_ids = line_vals

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

    def action_apply(self):
        """Apply the renegotiation to the invoice."""
        self.ensure_one()
        self._validate_renegotiation()

        move = self.move_id

        # Capture original state for audit trail
        original_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term" and not line.reconciled
        )
        old_lines_data = [
            {
                "date_maturity": line.date_maturity,
                "amount_currency": line.amount_currency,
            }
            for line in original_lines.sorted("date_maturity")
        ]

        # Determine the sign for amounts (positive for receivable, negative for payable)
        sign = 1 if move.is_inbound() else -1

        # Prepare context for bypassing readonly restrictions
        ctx = dict(
            self.env.context,
            skip_invoice_sync=True,
            allow_installment_renegotiation=True,
            check_move_validity=False,
        )

        # Get the receivable/payable account from existing lines
        account_id = original_lines[0].account_id.id

        # Build list of operations: update, create, delete
        wizard_lines = self.line_ids.sorted("date_maturity")
        original_lines_list = list(original_lines.sorted("date_maturity"))

        # Prepare new line values
        new_line_vals = []
        for wiz_line in wizard_lines:
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

            new_line_vals.append(
                {
                    "date_maturity": wiz_line.date_maturity,
                    "amount_currency": amount_currency,
                    "debit": balance if balance > 0 else 0,
                    "credit": -balance if balance < 0 else 0,
                    "account_id": account_id,
                    "original_line_id": wiz_line.original_line_id.id,
                }
            )

        # Apply changes within context
        move.with_context(**ctx).sudo()

        # Strategy: Update existing lines where possible, create new ones if needed,
        # delete excess ones
        lines_to_keep = []
        lines_to_create = []

        for i, vals in enumerate(new_line_vals):
            if i < len(original_lines_list):
                # Update existing line
                line = original_lines_list[i].with_context(**ctx)
                line.sudo().write(
                    {
                        "date_maturity": vals["date_maturity"],
                        "amount_currency": vals["amount_currency"],
                        "debit": vals["debit"],
                        "credit": vals["credit"],
                    }
                )
                lines_to_keep.append(line.id)
            else:
                # Need to create new line
                lines_to_create.append(vals)

        # Delete excess lines (if we reduced the number of installments)
        lines_to_delete = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
            and not line.reconciled
            and line.id not in lines_to_keep
        )
        if lines_to_delete:
            # Use force_delete=True to bypass the posted entry deletion constraint
            lines_to_delete.with_context(
                **ctx, dynamic_unlink=True, force_delete=True
            ).sudo().unlink()

        # Create new lines if needed
        if lines_to_create:
            for vals in lines_to_create:
                self.env["account.move.line"].with_context(**ctx).sudo().create(
                    {
                        "move_id": move.id,
                        "display_type": "payment_term",
                        "name": "",
                        "account_id": vals["account_id"],
                        "date_maturity": vals["date_maturity"],
                        "amount_currency": vals["amount_currency"],
                        "debit": vals["debit"],
                        "credit": vals["credit"],
                        "currency_id": move.currency_id.id,
                        "partner_id": move.partner_id.id,
                    }
                )

        # Update payment term numbering and labels
        move.with_context(**ctx).update_payment_term_number()

        # Capture new state for audit trail
        new_lines = move.line_ids.filtered(
            lambda line: line.display_type == "payment_term" and not line.reconciled
        )
        new_lines_data = [
            {
                "date_maturity": line.date_maturity,
                "amount_currency": line.amount_currency,
            }
            for line in new_lines.sorted("date_maturity")
        ]

        # Post message to chatter
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
