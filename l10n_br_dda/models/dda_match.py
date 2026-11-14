# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants import DEBIT_MODEL, MATCH_MODEL


class DdaMatch(models.Model):
    _name = MATCH_MODEL
    _description = "DDA boleto suggestion"
    _order = "score desc, id"

    debit_id = fields.Many2one(
        comodel_name=DEBIT_MODEL, required=True, ondelete="cascade", index=True
    )
    company_id = fields.Many2one(related="debit_id.company_id", store=True)
    currency_id = fields.Many2one(related="debit_id.currency_id")
    move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="l10n_br_dda_match_move_line_rel",
        column1="match_id",
        column2="move_line_id",
        string="Payable lines",
    )
    is_multi = fields.Boolean(
        string="Several installments",
        help="One boleto for several installments of the same vendor.",
    )
    score = fields.Integer()
    identity_kind = fields.Selection(
        selection=[
            ("full", "Same CNPJ"),
            ("assignment", "Assignment"),
            ("root", "Same CNPJ root"),
        ]
    )
    is_strict = fields.Boolean(
        string="Strict rule",
        help="The suggestion satisfies the rule of the automatic link.",
    )
    amount_total = fields.Monetary(
        currency_field="currency_id",
        help="Sum of the open amounts of the payable lines.",
    )
    amount_diff = fields.Monetary(
        currency_field="currency_id",
        help="Boleto amount minus the open amount of the lines.",
    )
    date_diff = fields.Integer(
        help="Days between the due dates of the boleto and the title; -1 if unknown."
    )
    evidence = fields.Text(help="Why the suggestion was made, one reason per line.")
    label = fields.Char(compute="_compute_label")

    @api.depends("move_line_ids", "is_multi")
    def _compute_label(self):
        for match in self:
            names = []
            for line in match.move_line_ids:
                names.append(line.document_number or line.move_id.name or "")
            match.label = ", ".join(n for n in names if n)
