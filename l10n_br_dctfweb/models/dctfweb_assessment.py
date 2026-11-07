# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import json
from calendar import monthrange
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import (
    MIT_GROUP_JSON_KEY,
    MIT_MONETARY_VARIATION,
    MIT_MONTH,
    MIT_PIS_COFINS_REGIME,
    MIT_PJ_QUALIFICATION,
    MIT_PROFIT_TAXATION,
)

# The MIT only exists for facts generated from January 2025 on: before that the
# debits were confessed in the DCTF PGD (IN RFB 2.237/2024, art. 19).
MIT_FIRST_YEAR = 2025


class DctfwebAssessment(models.Model):
    """One MIT assessment: the federal debits of a company in one month.

    The MIT is the DCTFWeb generating bookkeeping for the debits that used to
    be confessed in the DCTF PGD (IN RFB 2.237/2024, art. 9). This model does
    not compute a single tax: it reads what the tax assessment already
    persisted and turns it into a confession, so the escrituracao, the books
    and the confession cannot diverge.
    """

    _name = "l10n_br_dctfweb.assessment"
    _description = "DCTFWeb/MIT Assessment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "year desc, month desc, rectification_sequence desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        readonly=True,
    )
    year = fields.Integer(
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: fields.Date.context_today(self).year,
        help="AnoApuracao: the year of the assessment period.",
    )
    month = fields.Selection(
        selection=MIT_MONTH,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: str(fields.Date.context_today(self).month),
        help="MesApuracao: the month of the assessment period.",
    )
    date_from = fields.Date(compute="_compute_dates", store=True)
    date_to = fields.Date(compute="_compute_dates", store=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("assessed", "Assessed"),
            ("closed", "Closed"),
            ("transmitted", "Transmitted"),
        ],
        required=True,
        default="draft",
        tracking=True,
        help="Closed means the local assessment is final and the JSON is "
        "built. Transmitted means the authority accepted it.",
    )
    no_movement = fields.Boolean(
        string="Without movement",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="SemMovimento: no taxable fact in the period. A company files it "
        "once and only files again when there is movement.",
    )

    # DadosIniciais
    pj_qualification = fields.Selection(
        selection=MIT_PJ_QUALIFICATION,
        string="Legal entity qualification",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    profit_taxation = fields.Selection(
        selection=MIT_PROFIT_TAXATION,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    monetary_variation = fields.Selection(
        selection=MIT_MONETARY_VARIATION,
        string="Monetary variation criterion",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    pis_cofins_regime = fields.Selection(
        selection=MIT_PIS_COFINS_REGIME,
        string="PIS/COFINS regime",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    real_profit_balance = fields.Boolean(
        string="Suspension or reduction balance sheet",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="BalancoLucroReal: the entity raised a suspension or reduction "
        "balance sheet in the month. Only for annual actual profit.",
    )

    # ResponsavelApuracao
    responsible_cpf = fields.Char(size=11, string="Responsible CPF")
    responsible_phone_area = fields.Char(size=2, string="Phone area code")
    responsible_phone = fields.Char(size=9, string="Phone number")
    responsible_email = fields.Char(size=60, string="Responsible e-mail")
    crc_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="CRC state",
        domain="[('country_id.code', '=', 'BR')]",
    )
    crc_number = fields.Char(size=11, string="CRC number")

    debit_ids = fields.One2many(
        comodel_name="l10n_br_dctfweb.debit",
        inverse_name="assessment_id",
        string="Debits",
    )
    suspension_ids = fields.One2many(
        comodel_name="l10n_br_dctfweb.suspension",
        inverse_name="assessment_id",
        string="Suspensions",
    )
    special_event_ids = fields.One2many(
        comodel_name="l10n_br_dctfweb.special.event",
        inverse_name="assessment_id",
        string="Special events",
    )
    tax_assessment_ids = fields.Many2many(
        comodel_name="l10n_br_tax.assessment",
        string="Tax assessments",
        readonly=True,
        help="The persisted assessments this confession was read from.",
    )
    debit_total = fields.Monetary(compute="_compute_debit_total", store=True)
    suspended_total = fields.Monetary(compute="_compute_debit_total", store=True)

    rectification_of_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.assessment",
        string="Rectifies",
        readonly=True,
        copy=False,
    )
    rectification_sequence = fields.Integer(
        readonly=True,
        default=0,
        copy=False,
        help="Zero for the original assessment, then one per rectification.",
    )
    mit_file = fields.Binary(
        string="MIT file", readonly=True, copy=False, attachment=True
    )
    mit_filename = fields.Char(readonly=True, copy=False)

    _sql_constraints = [
        (
            "unique_period_company",
            "unique(company_id, year, month, rectification_sequence)",
            "This company already has an assessment for this period.",
        )
    ]

    @api.depends("year", "month", "rectification_sequence")
    def _compute_name(self):
        for record in self:
            if not record.year or not record.month:
                record.name = _("New assessment")
                continue
            name = f"MIT {record.month.zfill(2)}/{record.year}"
            if record.rectification_sequence:
                name = f"{name} ({record.rectification_sequence})"
            record.name = name

    @api.depends("year", "month")
    def _compute_dates(self):
        for record in self:
            if not record.year or not record.month:
                record.date_from = record.date_to = False
                continue
            month = int(record.month)
            record.date_from = date(record.year, month, 1)
            record.date_to = date(record.year, month, monthrange(record.year, month)[1])

    @api.depends("debit_ids.amount", "suspension_ids.line_ids.amount")
    def _compute_debit_total(self):
        for record in self:
            record.debit_total = sum(record.debit_ids.mapped("amount"))
            record.suspended_total = sum(
                record.suspension_ids.mapped("line_ids.amount")
            )

    @api.constrains("year")
    def _check_year(self):
        for record in self:
            if record.year and record.year < MIT_FIRST_YEAR:
                raise UserError(
                    _(
                        "The MIT only covers facts generated from %s on. "
                        "Earlier periods were confessed in the DCTF PGD."
                    )
                    % MIT_FIRST_YEAR
                )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        """Bring the company defaults, which rarely change from month to month."""
        for record in self:
            company = record.company_id
            if not company:
                continue
            record.pj_qualification = company.dctfweb_pj_qualification
            record.profit_taxation = company.dctfweb_profit_taxation
            record.monetary_variation = company.dctfweb_monetary_variation
            record.pis_cofins_regime = company.dctfweb_pis_cofins_regime
            record.responsible_cpf = company.dctfweb_responsible_cpf
            record.responsible_phone_area = company.dctfweb_responsible_phone_area
            record.responsible_phone = company.dctfweb_responsible_phone
            record.responsible_email = company.dctfweb_responsible_email
            record.crc_state_id = company.dctfweb_crc_state_id
            record.crc_number = company.dctfweb_crc_number

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "company_id" not in vals:
                continue
            company = self.env["res.company"].browse(vals["company_id"])
            for field, source in self._company_default_map().items():
                vals.setdefault(field, company[source])
        return super().create(vals_list)

    @api.model
    def _company_default_map(self):
        return {
            "pj_qualification": "dctfweb_pj_qualification",
            "profit_taxation": "dctfweb_profit_taxation",
            "monetary_variation": "dctfweb_monetary_variation",
            "pis_cofins_regime": "dctfweb_pis_cofins_regime",
            "responsible_cpf": "dctfweb_responsible_cpf",
            "responsible_phone_area": "dctfweb_responsible_phone_area",
            "responsible_phone": "dctfweb_responsible_phone",
            "responsible_email": "dctfweb_responsible_email",
            "crc_state_id": "dctfweb_crc_state_id",
            "crc_number": "dctfweb_crc_number",
        }

    # ------------------------------------------------------------------
    # Assessment
    # ------------------------------------------------------------------

    def _tax_assessment_domain(self):
        """The persisted assessments that fall inside this MIT period.

        Only assessments already computed or closed are read: a draft one has
        no total yet. The period has to be contained in the month, because the
        MIT is monthly and a longer tax assessment would smear two months.
        """
        self.ensure_one()
        return [
            ("company_id", "=", self.company_id.id),
            ("date_from", ">=", self.date_from),
            ("date_to", "<=", self.date_to),
            ("state", "in", ("computed", "posted")),
        ]

    def _read_tax_assessments(self):
        self.ensure_one()
        assessments = self.env["l10n_br_tax.assessment"].search(
            self._tax_assessment_domain()
        )
        without_code = assessments.filtered(
            lambda a: not a.tax_group_id.dctfweb_revenue_code_id
        )
        if without_code:
            self.message_post(
                body=_(
                    "These assessments were skipped because their tax group "
                    "has no MIT revenue code: %s"
                )
                % ", ".join(without_code.mapped("name"))
            )
        return assessments - without_code

    def _prepare_debit_from_tax_assessment(self, assessment):
        """One debit line per persisted assessment.

        The confessed amount is the assessed balance, field 11 of the E110,
        not the amount payable: withholding and deduction are matched against
        the debit inside the DCTFWeb, they do not shrink the confession.
        """
        self.ensure_one()
        code = assessment.tax_group_id.dctfweb_revenue_code_id
        values = {
            "assessment_id": self.id,
            "revenue_code_id": code.id,
            "amount": assessment.assessed_balance,
            "source": "computed",
            "tax_assessment_id": assessment.id,
        }
        if code.requires_establishment:
            values["establishment_cnpj"] = self._establishment_cnpj(
                assessment.company_id
            )
        return values

    @api.model
    def _establishment_cnpj(self, company):
        """The last 6 digits of the establishment CNPJ, order number plus check."""
        digits = "".join(filter(str.isdigit, company.cnpj_cpf or ""))
        return digits[-6:] if len(digits) == 14 else False

    def action_assess(self):
        """Read the persisted tax assessments into MIT debits."""
        for record in self:
            if record.state not in ("draft", "assessed"):
                raise UserError(
                    _("Only a draft or assessed MIT can be assessed again.")
                )
            record.debit_ids.filtered(lambda d: d.source == "computed").unlink()
            if record.no_movement:
                record.tax_assessment_ids = [fields.Command.clear()]
                record.state = "assessed"
                continue
            assessments = record._read_tax_assessments()
            values = [
                record._prepare_debit_from_tax_assessment(assessment)
                for assessment in assessments
                if assessment.assessed_balance
            ]
            self.env["l10n_br_dctfweb.debit"].create(values)
            record.tax_assessment_ids = [fields.Command.set(assessments.ids)]
            record.state = "assessed"
        return True

    # ------------------------------------------------------------------
    # Pendency check, the manual's item 3.6
    # ------------------------------------------------------------------

    def _check_pendencies(self):
        """Return the list of reasons this assessment cannot be closed."""
        self.ensure_one()
        pendencies = []
        if not self.pj_qualification:
            pendencies.append(_("The legal entity qualification is required."))
        if not self.responsible_cpf:
            pendencies.append(_("The CPF of the responsible is required."))
        elif len("".join(filter(str.isdigit, self.responsible_cpf))) != 11:
            pendencies.append(_("The CPF of the responsible must have 11 digits."))
        if not self._company_cnpj_root():
            pendencies.append(
                _("The company %s has no valid CNPJ.") % self.company_id.display_name
            )
        if self.no_movement:
            if self.debit_ids:
                pendencies.append(
                    _("An assessment without movement cannot carry debits.")
                )
            return pendencies
        if self.pj_qualification != "11" and not self.profit_taxation:
            pendencies.append(_("The profit taxation form is required."))
        if not self.monetary_variation:
            pendencies.append(_("The monetary variation criterion is required."))
        if not self.debit_ids:
            pendencies.append(
                _(
                    "An assessment with movement needs at least one debit. "
                    "Tick 'Without movement' if there was no taxable fact."
                )
            )
        for debit in self.debit_ids:
            pendencies.extend(debit._check_layout())
        for suspension in self.suspension_ids:
            pendencies.extend(suspension._check_layout())
        return pendencies

    def action_close(self):
        """Freeze the assessment and build the MIT file."""
        for record in self:
            if record.state != "assessed":
                raise UserError(_("Assess the MIT before closing it."))
            pendencies = record._check_pendencies()
            if pendencies:
                raise UserError(
                    _("The MIT %(name)s cannot be closed:\n%(pendencies)s")
                    % {
                        "name": record.name,
                        "pendencies": "\n".join("- %s" % p for p in pendencies),
                    }
                )
            payload = record._build_mit_payload()
            record.write(
                {
                    "mit_file": base64.b64encode(
                        json.dumps(payload, ensure_ascii=False, indent=2).encode()
                    ),
                    "mit_filename": record._mit_filename(),
                    "state": "closed",
                }
            )
        return True

    def action_draft(self):
        for record in self:
            if record.state == "transmitted":
                raise UserError(
                    _("A transmitted MIT cannot go back to draft. Rectify it instead.")
                )
            record.write({"state": "draft", "mit_file": False, "mit_filename": False})
        return True

    def action_rectify(self):
        """Open a new assessment that rectifies this one."""
        self.ensure_one()
        if self.state != "transmitted":
            raise UserError(_("Only a transmitted MIT can be rectified."))
        last = self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("year", "=", self.year),
                ("month", "=", self.month),
            ],
            order="rectification_sequence desc",
            limit=1,
        )
        rectification = self.copy(
            {
                "rectification_of_id": self.id,
                "rectification_sequence": last.rectification_sequence + 1,
                "state": "draft",
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": rectification.id,
            "view_mode": "form",
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def _company_cnpj_root(self):
        """The 8 first digits of the company CNPJ, which name the file."""
        self.ensure_one()
        digits = "".join(filter(str.isdigit, self.company_id.cnpj_cpf or ""))
        return digits[:8] if len(digits) == 14 else False

    def _mit_filename(self):
        self.ensure_one()
        root = self._company_cnpj_root()
        return f"{root}-MIT-{self.year}{self.month.zfill(2)}.json"

    def _build_initial_data(self):
        self.ensure_one()
        responsible = {"CpfResponsavel": self.responsible_cpf}
        if self.responsible_phone_area and self.responsible_phone:
            responsible["TelResponsavel"] = {
                "Ddd": self.responsible_phone_area,
                "NumTelefone": self.responsible_phone,
            }
        if self.responsible_email:
            responsible["EmailResponsavel"] = self.responsible_email
        if self.crc_state_id and self.crc_number:
            responsible["RegistroCrc"] = {
                "UfRegistro": self.crc_state_id.code,
                "NumRegistro": self.crc_number,
            }
        data = {
            "SemMovimento": self.no_movement,
            "QualificacaoPj": int(self.pj_qualification),
            "ResponsavelApuracao": responsible,
        }
        if not self.no_movement:
            if self.profit_taxation:
                data["TributacaoLucro"] = int(self.profit_taxation)
            if self.monetary_variation:
                data["VariacoesMonetarias"] = int(self.monetary_variation)
            if self.pis_cofins_regime:
                data["RegimePisCofins"] = int(self.pis_cofins_regime)
        return data

    def _build_debits(self):
        """Group the debits by tax group, in the order the layout requires."""
        self.ensure_one()
        debits = {}
        if self.profit_taxation == "1" and not self.special_event_ids:
            debits["BalancoLucroReal"] = self.real_profit_balance
        for group, json_key in MIT_GROUP_JSON_KEY.items():
            lines = self.debit_ids.filtered(
                lambda d, group=group: d.revenue_code_id.group == group
            )
            if not lines:
                continue
            after_event = lines.filtered("after_special_event")
            regular = lines - after_event
            group_payload = {}
            if regular:
                group_payload["ListaDebitos"] = [
                    line._build_payload() for line in regular
                ]
            if after_event:
                group_payload["ListaDebitosAposEvento"] = [
                    line._build_payload() for line in after_event
                ]
            debits[json_key] = group_payload
        return debits

    def _build_mit_payload(self):
        """The whole MIT JSON, layout 1.0 (ADE CORAT 19/2024)."""
        self.ensure_one()
        payload = {
            "PeriodoApuracao": {
                "MesApuracao": int(self.month),
                "AnoApuracao": self.year,
            },
            "DadosIniciais": self._build_initial_data(),
        }
        if self.special_event_ids:
            payload["ListaEventosEspeciais"] = [
                event._build_payload() for event in self.special_event_ids.sorted("day")
            ]
        if not self.no_movement:
            debits = self._build_debits()
            if debits:
                payload["Debitos"] = debits
            if self.suspension_ids:
                payload["ListaSuspensoes"] = [
                    suspension._build_payload() for suspension in self.suspension_ids
                ]
        return payload

    def action_export_json(self):
        """Rebuild the file and hand it over as a download."""
        self.ensure_one()
        if self.state == "draft":
            raise UserError(_("Assess the MIT before exporting it."))
        payload = self._build_mit_payload()
        self.write(
            {
                "mit_file": base64.b64encode(
                    json.dumps(payload, ensure_ascii=False, indent=2).encode()
                ),
                "mit_filename": self._mit_filename(),
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model={self._name}&id={self.id}"
            "&field=mit_file&filename_field=mit_filename&download=true",
            "target": "self",
        }
