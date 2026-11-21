# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_date


class ResultClosingWizard(models.TransientModel):
    _name = "l10n_br_account.result.closing.wizard"
    _description = "Close the result of the period"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        required=True,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        compute="_compute_journal_id",
        store=True,
        precompute=True,
        readonly=False,
    )
    equity_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Equity Account",
        required=True,
        domain="[('internal_group', '=', 'equity'),"
        " ('company_ids', 'parent_of', company_id)]",
        compute="_compute_equity_account_id",
        store=True,
        precompute=True,
        readonly=False,
        help="Account of the equity that receives the result, such as the "
        "accumulated profits or losses. It comes from the last closing of the "
        "company.",
    )

    @api.depends("company_id")
    def _compute_journal_id(self):
        for wizard in self:
            last = wizard._last_closing()
            wizard.journal_id = last.journal_id or self.env["account.journal"].search(
                [("type", "=", "general"), ("company_id", "=", wizard.company_id.id)],
                limit=1,
            )

    @api.depends("company_id")
    def _compute_equity_account_id(self):
        for wizard in self:
            wizard.equity_account_id = (
                wizard._last_closing()
                .line_ids.filtered(
                    lambda line: line.account_id.internal_group == "equity"
                )[:1]
                .account_id
            )

    def _last_closing(self):
        return self.env["account.move"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("l10n_br_sped_result_closing", "=", True),
                ("state", "=", "posted"),
            ],
            order="date desc, id desc",
            limit=1,
        )

    def _result_balances(self):
        groups = self.env["account.move.line"]._read_group(
            [
                ("company_id", "=", self.company_id.id),
                ("parent_state", "=", "posted"),
                ("move_id.l10n_br_sped_result_closing", "=", False),
                ("account_id.internal_group", "in", ("income", "expense")),
                ("date", ">=", self.date_from),
                ("date", "<=", self.date_to),
            ],
            groupby=["account_id"],
            aggregates=["balance:sum"],
        )
        currency = self.company_id.currency_id
        return {
            account.id: currency.round(balance)
            for account, balance in groups
            if not currency.is_zero(balance)
        }

    def action_close(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("The start date is after the end date."))
        closed = self.env["account.move"].search_count(
            [
                ("company_id", "=", self.company_id.id),
                ("l10n_br_sped_result_closing", "=", True),
                ("state", "!=", "cancel"),
                ("date", ">=", self.date_from),
                ("date", "<=", self.date_to),
            ]
        )
        if closed:
            raise UserError(_("The result of this period is already closed."))
        balances = self._result_balances()
        if not balances:
            raise UserError(_("There is no result to close in this period."))
        label = _(
            "Closing of the result from %(date_from)s to %(date_to)s",
            date_from=format_date(self.env, self.date_from),
            date_to=format_date(self.env, self.date_to),
        )
        lines = [
            (0, 0, {"account_id": account, "name": label, "balance": -balance})
            for account, balance in balances.items()
        ]
        lines.append(
            (
                0,
                0,
                {
                    "account_id": self.equity_account_id.id,
                    "name": label,
                    "balance": sum(balances.values()),
                },
            )
        )
        move = (
            self.env["account.move"]
            .with_company(self.company_id)
            .create(
                {
                    "move_type": "entry",
                    "date": self.date_to,
                    "ref": label,
                    "journal_id": self.journal_id.id,
                    "company_id": self.company_id.id,
                    "l10n_br_sped_result_closing": True,
                    "line_ids": lines,
                }
            )
        )
        move.action_post()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
        }
