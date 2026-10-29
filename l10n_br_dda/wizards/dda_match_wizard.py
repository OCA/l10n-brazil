# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import DEBIT_MODEL


class DdaMatchWizard(models.TransientModel):
    _name = "l10n_br_dda.match.wizard"
    _description = "Link a DDA boleto to payable lines"

    debit_id = fields.Many2one(
        comodel_name=DEBIT_MODEL, required=True, ondelete="cascade"
    )
    company_id = fields.Many2one(related="debit_id.company_id")
    currency_id = fields.Many2one(related="debit_id.currency_id")
    beneficiary_name = fields.Char(related="debit_id.beneficiary_name")
    beneficiary_vat = fields.Char(related="debit_id.beneficiary_vat")
    guarantor_name = fields.Char(related="debit_id.guarantor_name")
    boleto_amount = fields.Monetary(
        related="debit_id.amount", currency_field="currency_id"
    )
    boleto_due = fields.Date(related="debit_id.date_due")
    boleto_number = fields.Char(related="debit_id.document_number")
    candidate_ids = fields.One2many(
        comodel_name="l10n_br_dda.match.wizard.line",
        inverse_name="wizard_id",
        string="Candidates",
    )
    extra_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        string="Other titles",
        domain="[('company_id', '=', company_id), "
        "('account_id.account_type', '=', 'liability_payable'), "
        "('reconciled', '=', False), ('parent_state', '=', 'posted')]",
        help="Search another payable line of the company.",
    )
    due_policy = fields.Selection(
        selection=[
            ("keep", "Keep the data of the title"),
            ("update", "Update the due date of the title"),
        ],
        default="keep",
        required=True,
        help="When the due dates differ. The amount is never changed: the "
        "difference goes to the write-off.",
    )
    total_selected = fields.Monetary(
        compute="_compute_total_selected", currency_field="currency_id"
    )

    def _load_candidates(self):
        self.ensure_one()
        lines = []
        for match in self.debit_id.match_ids:
            lines.append(
                (
                    0,
                    0,
                    {
                        "match_id": match.id,
                        "move_line_ids": [(6, 0, match.move_line_ids.ids)],
                        "score": match.score,
                        "evidence": match.evidence,
                        "amount_total": match.amount_total,
                        "amount_diff": match.amount_diff,
                        "date_diff": match.date_diff,
                        "selected": False,
                    },
                )
            )
        self.candidate_ids = lines

    @api.depends("candidate_ids.selected", "extra_line_ids")
    def _compute_total_selected(self):
        for wizard in self:
            lines = wizard._selected_lines()
            wizard.total_selected = sum(-line.amount_residual for line in lines)

    def _selected_lines(self):
        self.ensure_one()
        lines = self.candidate_ids.filtered("selected").move_line_ids
        return lines | self.extra_line_ids

    def action_confirm(self):
        self.ensure_one()
        lines = self._selected_lines()
        if not lines:
            raise UserError(_("Select at least one title."))
        self.debit_id.action_link(lines.ids, update_due=self.due_policy == "update")
        return {"type": "ir.actions.act_window_close"}

    def action_create_bill(self):
        self.ensure_one()
        self.debit_id.action_create_bill()
        return {"type": "ir.actions.act_window_close"}


class DdaMatchWizardLine(models.TransientModel):
    _name = "l10n_br_dda.match.wizard.line"
    _description = "Candidate title of the DDA link wizard"
    _order = "score desc, id"

    wizard_id = fields.Many2one(
        comodel_name="l10n_br_dda.match.wizard", required=True, ondelete="cascade"
    )
    currency_id = fields.Many2one(related="wizard_id.currency_id")
    match_id = fields.Many2one(comodel_name="l10n_br_dda.match")
    move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="l10n_br_dda_match_wizard_line_move_line_rel",
        column1="wizard_line_id",
        column2="move_line_id",
        string="Titles",
    )
    score = fields.Integer()
    evidence = fields.Text()
    amount_total = fields.Monetary(currency_field="currency_id")
    amount_diff = fields.Monetary(currency_field="currency_id")
    date_diff = fields.Integer()
    selected = fields.Boolean()
