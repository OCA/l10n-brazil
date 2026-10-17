# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import MIT_POSTPONED_EXTENSION


class DctfwebDebit(models.Model):
    """One confessed debit of a MIT assessment.

    The layout carries no base and no rate: a debit is a revenue code and an
    amount, plus the attributes that code demands. Everything that explains
    the amount stays in the tax assessment this line came from.
    """

    _name = "l10n_br_dctfweb.debit"
    _description = "DCTFWeb/MIT Debit"
    _order = "assessment_id, revenue_code_id, id"

    assessment_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.assessment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="assessment_id.company_id",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="assessment_id.currency_id",
        readonly=True,
    )
    revenue_code_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.revenue.code",
        required=True,
        ondelete="restrict",
    )
    group = fields.Selection(
        related="revenue_code_id.group",
        store=True,
        readonly=True,
    )
    periodicity = fields.Selection(
        related="revenue_code_id.periodicity",
        store=True,
        readonly=True,
    )
    debit_number = fields.Integer(
        compute="_compute_debit_number",
        store=True,
        help="IdDebito: unique and sequential inside the assessment. The "
        "suspensions point at this number.",
    )
    special_event_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.special.event",
        string="Special event",
        ondelete="set null",
        help="IdEventoDebito: the event up to whose date the taxable facts "
        "of this debit were considered.",
    )
    after_special_event = fields.Boolean(
        help="The taxable fact happened after the last special event of the "
        "month, so the debit goes to ListaDebitosAposEvento.",
    )
    period = fields.Integer(
        string="Period of the debit",
        help="PaDebito: the day for a daily code, the ten-day period for a "
        "ten-day code.",
    )
    postponed_year = fields.Integer(
        help="AnoPostergado: year of the postponed IRPJ or CSLL period.",
    )
    postponed_quarter = fields.Selection(
        selection=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4")],
        help="TrimPostergado: quarter of the postponed period.",
    )
    debit_year = fields.Integer(
        help="AnoDebito: year of the annual IRPJ or CSLL adjustment.",
    )
    establishment_cnpj = fields.Char(
        size=6,
        help="CnpjEstabelecimento: the 6 digits after the CNPJ root.",
    )
    incorporation_cnpj = fields.Char(
        size=14,
        help="CnpjIncorporacao: 6 digits for an establishment of the company, "
        "or the whole 14 digit CNPJ for a joint venture development.",
    )
    scp_cnpj = fields.Char(
        size=14,
        string="SCP CNPJ",
        help="CnpjScp: the 14 digit CNPJ of the unincorporated joint venture.",
    )
    gold_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Gold origin city",
        domain="[('country_id.code', '=', 'BR')]",
        help="CodigoMunicipioOuro: the city the gold was produced in.",
    )
    amount = fields.Monetary(
        string="Debit amount",
        required=True,
        help="ValorDebito: the assessed amount of the debit.",
    )
    source = fields.Selection(
        selection=[
            ("computed", "Read from the tax assessment"),
            ("manual", "Manual"),
        ],
        required=True,
        default="manual",
    )
    tax_assessment_id = fields.Many2one(
        comodel_name="l10n_br_tax.assessment",
        string="Tax assessment",
        readonly=True,
        ondelete="set null",
        help="The persisted assessment this amount was read from.",
    )

    @api.depends("assessment_id.debit_ids")
    def _compute_debit_number(self):
        for assessment in self.mapped("assessment_id"):
            for number, debit in enumerate(assessment.debit_ids, start=1):
                debit.debit_number = number
        for debit in self.filtered(lambda d: not d.assessment_id):
            debit.debit_number = 0

    @api.constrains("amount")
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(
                    _("The debit of %s must be positive.")
                    % record.revenue_code_id.display_name
                )

    def _check_layout(self):
        """Return the layout pendencies of this debit.

        This is the check the authority's own application does before letting
        the assessment be closed: an attribute the revenue code demands and
        that nobody filled in.
        """
        self.ensure_one()
        pendencies = []
        code = self.revenue_code_id
        label = code.display_name
        if code.requires_period and not self.period:
            pendencies.append(
                _("The debit %s needs the period of the debit (PaDebito).") % label
            )
        if self.period:
            limit = {"daily": 31, "ten_day": 3}.get(code.periodicity)
            if limit and not 1 <= self.period <= limit:
                pendencies.append(
                    _(
                        "The period of the debit %(label)s must be between "
                        "1 and %(limit)s."
                    )
                    % {"label": label, "limit": limit}
                )
        if code.requires_establishment and not self.establishment_cnpj:
            pendencies.append(_("The debit %s needs the establishment CNPJ.") % label)
        if code.requires_incorporation and not self.incorporation_cnpj:
            pendencies.append(_("The debit %s needs the incorporation CNPJ.") % label)
        if code.requires_gold_city and not self.gold_city_id:
            pendencies.append(_("The debit %s needs the gold origin city.") % label)
        if code.is_postponed and not self.postponed_year:
            pendencies.append(
                _("The debit %s needs the year of the postponed period.") % label
            )
        if (
            code.is_postponed
            and code.periodicity == "quarterly"
            and not self.postponed_quarter
        ):
            pendencies.append(
                _("The debit %s needs the quarter of the postponed period.") % label
            )
        if code.requires_establishment and self.establishment_cnpj:
            digits = "".join(filter(str.isdigit, self.establishment_cnpj))
            if len(digits) != 6:
                pendencies.append(
                    _("The establishment CNPJ of the debit %s must have 6 digits.")
                    % label
                )
        if self.scp_cnpj:
            digits = "".join(filter(str.isdigit, self.scp_cnpj))
            if len(digits) != 14:
                pendencies.append(
                    _("The SCP CNPJ of the debit %s must have 14 digits.") % label
                )
        if self.special_event_id and self.after_special_event:
            pendencies.append(
                _(
                    "The debit %s cannot point at a special event and be after "
                    "the last event at the same time."
                )
                % label
            )
        if self.assessment_id.special_event_ids and not (
            self.special_event_id or self.after_special_event
        ):
            pendencies.append(
                _(
                    "The assessment has special events, so the debit %s needs "
                    "the event its taxable facts were considered up to."
                )
                % label
            )
        return pendencies

    def _build_payload(self):
        """The debit as the layout writes it."""
        self.ensure_one()
        code = self.revenue_code_id
        payload = {
            "IdDebito": self.debit_number,
            "CodigoDebito": code.mit_code,
            "ValorDebito": round(self.amount, 2),
        }
        if self.special_event_id and not self.after_special_event:
            payload["IdEventoDebito"] = self.special_event_id.event_number
        if code.requires_period and self.period:
            payload["PaDebito"] = self.period
        if code.is_postponed and self.postponed_year:
            payload["AnoPostergado"] = self.postponed_year
            if self.postponed_quarter:
                payload["TrimPostergado"] = int(self.postponed_quarter)
        elif code.requires_debit_year and self.debit_year:
            payload["AnoDebito"] = self.debit_year
        if code.requires_establishment and self.establishment_cnpj:
            payload["CnpjEstabelecimento"] = self.establishment_cnpj
        if code.requires_incorporation and self.incorporation_cnpj:
            payload["CnpjIncorporacao"] = self.incorporation_cnpj
        if code.allows_scp and self.scp_cnpj:
            payload["CnpjScp"] = self.scp_cnpj
        if code.requires_gold_city and self.gold_city_id:
            payload["CodigoMunicipioOuro"] = self.gold_city_id.ibge_code
        return payload

    @api.onchange("revenue_code_id")
    def _onchange_revenue_code_id(self):
        """Clear what the new code does not carry, so no stale attribute ships."""
        for record in self:
            code = record.revenue_code_id
            if not code.requires_period:
                record.period = 0
            if not code.requires_establishment:
                record.establishment_cnpj = False
            if not code.requires_incorporation:
                record.incorporation_cnpj = False
            if not code.allows_scp:
                record.scp_cnpj = False
            if not code.requires_gold_city:
                record.gold_city_id = False
            if not code.is_postponed:
                record.postponed_year = 0
                record.postponed_quarter = False
            if not code.requires_debit_year:
                record.debit_year = 0
            if code.extension != MIT_POSTPONED_EXTENSION and record.postponed_year:
                record.postponed_year = 0
