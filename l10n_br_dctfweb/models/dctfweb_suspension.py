# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import MIT_SUSPENSION_REASON, MIT_SUSPENSION_TYPE

# MotivoSuspensao 2 is the judicial deposit of the full amount: the layout
# asks for ComDeposito only when the reason is something else.
MIT_REASON_FULL_DEPOSIT = "2"


class DctfwebSuspension(models.Model):
    """A lawsuit or administrative process that suspends a confessed debit.

    The debit is still confessed: what the suspension says is how much of it
    the authority cannot demand yet.
    """

    _name = "l10n_br_dctfweb.suspension"
    _description = "DCTFWeb/MIT Suspension"
    _order = "assessment_id, id"

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
    suspension_type = fields.Selection(
        selection=MIT_SUSPENSION_TYPE,
        required=True,
        default="1",
        help="TipoSuspensao.",
    )
    reason = fields.Selection(
        selection=MIT_SUSPENSION_REASON,
        help="MotivoSuspensao: only for a judicial suspension.",
    )
    with_deposit = fields.Boolean(
        help="ComDeposito: the judicial suspension has a deposit.",
    )
    process_number = fields.Char(
        size=20,
        required=True,
        help="NumeroProcesso: 20 digits for a lawsuit, 17 for an "
        "administrative process.",
    )
    third_party_process = fields.Boolean(
        help="ProcessoTerceiro: the lawsuit belongs to a third party, the "
        "taxpayer is not the plaintiff.",
    )
    decision_date = fields.Date(help="DataDecisao.")
    court_number = fields.Integer(help="VaraJudiciaria.")
    court_city_id = fields.Many2one(
        comodel_name="res.city",
        string="Court city",
        domain="[('country_id.code', '=', 'BR')]",
        help="CodigoMunicipioSj: the city the court sits in.",
    )
    line_ids = fields.One2many(
        comodel_name="l10n_br_dctfweb.suspension.line",
        inverse_name="suspension_id",
        string="Suspended debits",
    )
    amount_total = fields.Monetary(compute="_compute_amount_total", store=True)

    @api.depends("line_ids.amount")
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(record.line_ids.mapped("amount"))

    def _check_layout(self):
        """Return the layout pendencies of this suspension."""
        self.ensure_one()
        pendencies = []
        label = self.process_number or _("without number")
        digits = "".join(filter(str.isdigit, self.process_number or ""))
        if len(digits) not in (17, 20):
            pendencies.append(
                _(
                    "The process number %s must have 20 digits for a lawsuit "
                    "or 17 for an administrative process."
                )
                % label
            )
        if not self.line_ids:
            pendencies.append(
                _("The suspension %s needs at least one suspended debit.") % label
            )
        if self.suspension_type == "2":
            if not self.reason:
                pendencies.append(
                    _("The judicial suspension %s needs its reason.") % label
                )
            if not self.decision_date:
                pendencies.append(
                    _("The judicial suspension %s needs the decision date.") % label
                )
            if not self.court_number:
                pendencies.append(
                    _("The judicial suspension %s needs the court number.") % label
                )
            if not self.court_city_id:
                pendencies.append(
                    _("The judicial suspension %s needs the court city.") % label
                )
        if self.assessment_id.special_event_ids:
            pendencies.append(
                _(
                    "The layout does not accept a suspension in an assessment "
                    "that has special events."
                )
            )
        for line in self.line_ids:
            if line.amount > line.debit_id.amount:
                pendencies.append(
                    _(
                        "The suspended amount of the debit %s is larger than "
                        "the debit itself."
                    )
                    % line.debit_id.revenue_code_id.display_name
                )
        return pendencies

    def _build_payload(self):
        """The suspension as the layout writes it."""
        self.ensure_one()
        payload = {
            "TipoSuspensao": int(self.suspension_type),
            "NumeroProcesso": "".join(filter(str.isdigit, self.process_number or "")),
            "ListaDebitosSuspensos": [line._build_payload() for line in self.line_ids],
        }
        if self.suspension_type == "2":
            payload["MotivoSuspensao"] = int(self.reason)
            payload["ProcessoTerceiro"] = self.third_party_process
            payload["DataDecisao"] = int(self.decision_date.strftime("%Y%m%d"))
            payload["VaraJudiciaria"] = self.court_number
            payload["CodigoMunicipioSj"] = self.court_city_id.ibge_code
            if self.reason != MIT_REASON_FULL_DEPOSIT:
                payload["ComDeposito"] = self.with_deposit
        return payload


class DctfwebSuspensionLine(models.Model):
    """How much of one debit a suspension covers."""

    _name = "l10n_br_dctfweb.suspension.line"
    _description = "DCTFWeb/MIT Suspended Debit"
    _order = "suspension_id, id"

    suspension_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.suspension",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="suspension_id.company_id",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="suspension_id.currency_id",
        readonly=True,
    )
    debit_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.debit",
        string="Debit",
        required=True,
        ondelete="cascade",
        help="IdDebitoSuspenso: the debit this suspension covers.",
    )
    amount = fields.Monetary(
        string="Suspended amount",
        required=True,
        help="ValorSuspenso.",
    )

    @api.constrains("debit_id", "suspension_id")
    def _check_same_assessment(self):
        for record in self:
            if record.debit_id.assessment_id != record.suspension_id.assessment_id:
                raise ValidationError(
                    _("A suspension can only cover a debit of its own assessment.")
                )

    @api.constrains("amount")
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_("The suspended amount must be positive."))

    def _build_payload(self):
        self.ensure_one()
        return {
            "IdDebitoSuspenso": self.debit_id.debit_number,
            "ValorSuspenso": round(self.amount, 2),
        }
