# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants import (
    REINF_CALCULATION_LINE_STATES,
    REINF_TAXES_ON_CREDIT,
    REINF_WITHHOLDING_TAXES,
)


class ReinfCalculationLine(models.Model):
    """One withholding of one tax, on one payment or credit, of one nature.

    The grain is deliberate: the layout asks for a dtFG per infoPgto and the
    fact that triggers the withholding is not the same for every tax, so a line
    per (beneficiary, nature, tax, date) is the only grain that can answer both
    the income tax on the credit and the PCC on the payment without lying about
    one of them.
    """

    _name = "l10n_br_reinf.calculation.line"
    _description = "EFD-Reinf Calculation Line"
    _order = "partner_id, nature_income_id, tax, fg_date, id"

    calculation_id = fields.Many2one(
        comodel_name="l10n_br_reinf.calculation",
        string="Calculation",
        required=True,
        index=True,
        ondelete="cascade",
    )

    company_id = fields.Many2one(
        related="calculation_id.company_id",
        store=True,
        index=True,
    )

    currency_id = fields.Many2one(
        related="company_id.currency_id",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Beneficiary",
        required=True,
        index=True,
    )

    nature_income_id = fields.Many2one(
        comodel_name="l10n_br_reinf.nature.income",
        string="Nature of Income",
        index=True,
    )

    tax = fields.Selection(
        selection=REINF_WITHHOLDING_TAXES,
        required=True,
        index=True,
    )

    fg_date = fields.Date(
        string="Taxable Event Date",
        required=True,
        index=True,
        help="dtFG of the line: the date of the credit for the income tax, the "
        "date of the payment for PIS/PASEP, COFINS and CSLL.",
    )

    on_credit = fields.Boolean(
        string="Triggered by the Credit",
        compute="_compute_on_credit",
        store=True,
        help="Whether the taxable event of this tax is the credit and not the "
        "payment.",
    )

    base_amount = fields.Monetary(
        string="Base",
        currency_field="currency_id",
    )

    wh_amount = fields.Monetary(
        string="Withheld",
        currency_field="currency_id",
    )

    revenue_code = fields.Char(
        size=6,
        index=True,
        help="Revenue code (CR) this withholding is collected under, read from "
        "the mapping of the Annex I of the nature of income.",
    )

    divergence_amount = fields.Monetary(
        string="Divergence",
        currency_field="currency_id",
        help="Difference between what is declared on this line and what the "
        "accounting holds. On an aggregated line it is the cents of the "
        "rounding of the collapse.",
    )

    source_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Source Invoice",
        index=True,
        ondelete="cascade",
    )

    source_move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Source Line",
        index=True,
        ondelete="cascade",
    )

    source_payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="Source Payment",
        index=True,
        ondelete="set null",
    )

    event_id = fields.Many2one(
        comodel_name="l10n_br_reinf.event",
        string="Event",
        readonly=True,
        index=True,
        ondelete="set null",
        help="Event that declares this line. A competence split by the limits "
        "of the layout has more than one event per beneficiary, and this is "
        "what says which slice each line went to.",
    )

    darf_id = fields.Many2one(
        comodel_name="l10n_br_reinf.darf",
        string="DARF",
        readonly=True,
        index=True,
        ondelete="set null",
        help="Mirror of the DARF this withholding was grouped into.",
    )

    state = fields.Selection(
        selection=REINF_CALCULATION_LINE_STATES,
        default="ok",
        required=True,
        index=True,
    )

    manually_verified = fields.Boolean(
        help="Somebody looked at this line and confirmed it. Recomputing the "
        "calculation keeps it instead of throwing it away.",
    )

    note = fields.Char()

    @api.depends("tax")
    def _compute_on_credit(self):
        for line in self:
            line.on_credit = line.tax in REINF_TAXES_ON_CREDIT
