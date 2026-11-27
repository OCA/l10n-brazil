# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_assisted_assessment.constants import (
    DIVERGENCE_CREDIT_DENIED,
    LINE_CREDIT,
    TRIBUTE_CBS,
)
from odoo.addons.l10n_br_cbs_assisted_assessment.constants import (
    PAYMENT_TYPE_RAD,
    SERVICE_WITHHOLDINGS,
)

CREDIT_TAKES = "credits"
CREDIT_NONE = "no_credit"
CREDIT_PARTIAL = "partial"
CREDIT_UNKNOWN = "unknown"
CREDIT_STATUSES = [
    (CREDIT_TAKES, "Takes Credit"),
    (CREDIT_NONE, "Does Not Take Credit"),
    (CREDIT_PARTIAL, "Partial Credit"),
    (CREDIT_UNKNOWN, "No Credit Position"),
]

COLLECTION_WE_PAY = "we_pay"
COLLECTION_SUPPLIER = "collects"
COLLECTION_UNKNOWN = "unknown"
COLLECTION_STATUSES = [
    (COLLECTION_WE_PAY, "We Pay as Acquirer"),
    (COLLECTION_SUPPLIER, "Supplier Collects"),
    (COLLECTION_UNKNOWN, "No Collection Position"),
]

AMOUNT_FIELDS = (
    "inbound_cbs",
    "credit_appropriated",
    "credit_not_appropriable",
    "credit_suspended",
    "credit_denied",
    "rad_paid",
)


class CbsAssessmentSupplier(models.Model):
    _name = "l10n_br_cbs_assisted_assessment.supplier"
    _description = "CBS supplier in an assisted assessment period"
    _order = "period_id, tax_id, supplier_key, id"

    period_id = fields.Many2one(
        comodel_name="l10n_br_assisted_assessment.period",
        string="Period",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="period_id.company_id",
        store=True,
        index=True,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        ondelete="set null",
        index=True,
    )
    supplier_key = fields.Char(
        required=True,
        index=True,
        help="Normalized tax id of the supplier, or the partner or document "
        "key when the files did not bring a tax id.",
    )
    tax_id = fields.Char(
        string="Tax ID",
        help="Supplier tax id, digits only. A withholding without a fiscal "
        "document keeps the supplier tax id from the file.",
    )
    tax_framework = fields.Selection(
        related="partner_id.tax_framework",
        string="Tax Framework",
        help="Fiscal regime of the partner. It explains the row and does not "
        "decide the credit or the collection.",
    )
    inbound_cbs = fields.Monetary(
        string="Inbound CBS",
        help="CBS booked on authorized inbound documents of this supplier in "
        "the period.",
    )
    credit_appropriated = fields.Monetary(
        string="Appropriated Credit",
        help="Credit the tax administration marked as appropriated.",
    )
    credit_not_appropriable = fields.Monetary(
        string="Non-appropriable Credit",
        help="Credit marked as non-appropriable or expired.",
    )
    credit_suspended = fields.Monetary(string="Suspended Credit")
    credit_denied = fields.Monetary(
        string="Credit Not Granted",
        help="Booked credit the reconciliation reported as not granted.",
    )
    rad_paid = fields.Monetary(
        string="RAD Paid by Us",
        help="Principal of acquirer RAD withholdings for this supplier. A RAD "
        "that extinguished our own debit is not included.",
    )
    credit_status = fields.Selection(
        selection=CREDIT_STATUSES,
        string="Credit",
        required=True,
    )
    collection_status = fields.Selection(
        selection=COLLECTION_STATUSES,
        string="Collection",
        required=True,
    )

    _sql_constraints = [
        (
            "period_supplier_uniq",
            "unique(period_id, supplier_key)",
            "This supplier was already computed for the assessment period.",
        ),
    ]

    @api.depends("partner_id.display_name", "tax_id", "supplier_key")
    def _compute_display_name(self):
        for supplier in self:
            supplier.display_name = (
                supplier.partner_id.display_name
                or supplier.tax_id
                or supplier.supplier_key
                or _("Supplier")
            )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_computed()
        return super().create(vals_list)

    def write(self, vals):
        self._check_computed()
        return super().write(vals)

    def unlink(self):
        self._check_computed()
        return super().unlink()

    def _check_computed(self):
        """Rows are rebuilt from the files and are not edited by hand."""
        if not self.env.su:
            raise UserError(
                _("Supplier rows are computed from the CBS assessment files.")
            )

    def action_open(self):
        """Rebuild every visible CBS period and open the supplier list."""
        periods = self.env["l10n_br_assisted_assessment.period"].search(
            [("tribute", "=", TRIBUTE_CBS)]
        )
        self._refresh(periods)
        return self._window_action(
            [("period_id", "in", periods.ids)],
            _("CBS Suppliers"),
        )

    def _window_action(self, domain, name):
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": self._name,
            "view_mode": "list,form",
            "domain": domain,
            "context": {"create": False, "edit": False, "delete": False},
        }

    def _refresh(self, periods):
        """Replace the stored rows of ``periods`` with a fresh reading."""
        periods = periods.filtered(lambda period: period.tribute == TRIBUTE_CBS)
        if not periods:
            return self.browse()
        rows = []
        for period in periods:
            rows.extend(self._rows_for_period(period))
        self.sudo().search([("period_id", "in", periods.ids)]).unlink()
        if not rows:
            return self.browse()
        return self.sudo().create(rows)

    def _rows_for_period(self, period):
        buckets = {}
        vat_by_key = self._absorb_withholdings(period, buckets)
        self._absorb_credits(period, buckets, vat_by_key)
        self._absorb_denied(period, buckets, vat_by_key)
        self._absorb_inbound(period, buckets)
        tolerance = period.company_id.assessment_tolerance or 0.01
        rows = []
        for key, bucket in buckets.items():
            amounts = self._rounded_amounts(period, bucket)
            if not self._has_signal(amounts, tolerance):
                continue
            partner = bucket["partner"] or self._partner_by_tax_id(
                period.company_id, bucket["tax_id"]
            )
            rows.append(
                {
                    "period_id": period.id,
                    "partner_id": partner.id,
                    "supplier_key": key,
                    "tax_id": bucket["tax_id"],
                    "credit_status": self._credit_status(amounts, tolerance),
                    "collection_status": self._collection_status(amounts, tolerance),
                    **amounts,
                }
            )
        return rows

    def _absorb_withholdings(self, period, buckets):
        """Acquirer RAD only. A RAD that paid our own debit stays out.

        The supplier is the partner of the matched inbound document. The tax
        id from the file is the fallback when that document is missing.
        """
        lines = self.env["l10n_br_cbs_assisted_assessment.payment.line"].search(
            [
                ("period_id", "=", period.id),
                ("payment_id.service", "=", SERVICE_WITHHOLDINGS),
                ("payment_id.payment_type", "=", PAYMENT_TYPE_RAD),
            ]
        )
        vat_by_key = {}
        for line in lines:
            partner = line.document_id.partner_id
            tax_id = self._tax_id(partner.vat) or self._tax_id(line.counterparty_vat)
            key = self._supplier_key(partner, tax_id, line.document_key)
            if line.document_key and tax_id:
                vat_by_key.setdefault(line.document_key, tax_id)
            self._add(buckets, key, partner, rad_paid=line.amount_principal)
        return vat_by_key

    def _absorb_credits(self, period, buckets, vat_by_key):
        credit_lines = period.line_ids.filtered(
            lambda line: line.line_type == LINE_CREDIT
        )
        for line in credit_lines:
            partner = line.document_id.partner_id
            tax_id = self._tax_id(partner.vat) or vat_by_key.get(line.document_key)
            key = self._supplier_key(partner, tax_id or "", line.document_key)
            appropriation = self._appropriation(line)
            self._add(
                buckets,
                key,
                partner,
                credit_appropriated=appropriation.get("apropriado"),
                credit_not_appropriable=(
                    self._number(appropriation.get("inapropriavel"))
                    + self._number(appropriation.get("prescrito"))
                ),
                credit_suspended=appropriation.get("suspenso"),
            )

    def _absorb_denied(self, period, buckets, vat_by_key):
        denied = period.divergence_ids.filtered(
            lambda divergence: (
                divergence.divergence_type == DIVERGENCE_CREDIT_DENIED
                and divergence.line_type == LINE_CREDIT
            )
        )
        for divergence in denied:
            document = divergence.document_id or divergence.line_id.document_id
            partner = document.partner_id
            tax_id = self._tax_id(partner.vat) or vat_by_key.get(
                divergence.document_key
            )
            key = self._supplier_key(partner, tax_id or "", divergence.document_key)
            self._add(
                buckets,
                key,
                partner,
                credit_denied=divergence.local_value,
            )

    def _absorb_inbound(self, period, buckets):
        for line in period._local_document_lines([LINE_CREDIT]):
            document = line.document_id
            partner = document.partner_id
            key = self._supplier_key(partner, "", document.document_key)
            self._add(buckets, key, partner, inbound_cbs=line.cbs_value)

    def _add(self, buckets, key, partner, **amounts):
        if not key:
            return
        bucket = buckets.setdefault(key, self._empty_bucket())
        accepted = self._accepted_partner(key, partner)
        if accepted and not bucket["partner"]:
            bucket["partner"] = accepted
        if not key.startswith(("partner:", "document:")):
            bucket["tax_id"] = key
        for name, amount in amounts.items():
            bucket[name] += self._number(amount)

    def _accepted_partner(self, key, partner):
        if not partner:
            return self.env["res.partner"]
        if key.startswith("partner:"):
            return partner
        tax_id = self._tax_id(partner.vat)
        if tax_id and tax_id == key:
            return partner
        if key.startswith("document:") and not tax_id:
            return partner
        return self.env["res.partner"]

    def _empty_bucket(self):
        bucket = {"partner": self.env["res.partner"], "tax_id": ""}
        bucket.update({name: 0.0 for name in AMOUNT_FIELDS})
        return bucket

    def _partner_by_tax_id(self, company, tax_id):
        if not tax_id:
            return self.env["res.partner"]
        partners = self.env["res.partner"].search(
            [
                ("cnpj_cpf_stripped", "=", tax_id),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", company.id),
            ]
        )
        companies = partners.filtered("is_company") or partners
        return companies.sorted("id")[:1]

    def _rounded_amounts(self, period, bucket):
        currency = period.company_id.currency_id
        rounded = {}
        for name in AMOUNT_FIELDS:
            amount = bucket[name]
            rounded[name] = currency.round(amount) if currency else amount
        return rounded

    @staticmethod
    def _has_signal(amounts, tolerance):
        return any(amounts[name] > tolerance for name in AMOUNT_FIELDS)

    @staticmethod
    def _credit_status(amounts, tolerance):
        appropriated = amounts["credit_appropriated"]
        denied = amounts["credit_not_appropriable"] + amounts["credit_denied"]
        if appropriated > tolerance and denied > tolerance:
            return CREDIT_PARTIAL
        if appropriated > tolerance:
            return CREDIT_TAKES
        if denied > tolerance:
            return CREDIT_NONE
        return CREDIT_UNKNOWN

    @staticmethod
    def _collection_status(amounts, tolerance):
        if amounts["rad_paid"] > tolerance:
            return COLLECTION_WE_PAY
        if amounts["inbound_cbs"] > tolerance:
            return COLLECTION_SUPPLIER
        return COLLECTION_UNKNOWN

    def _supplier_key(self, partner, tax_id, document_key):
        tax_id = tax_id or self._tax_id(partner.vat if partner else "")
        if tax_id:
            return tax_id
        if partner:
            return f"partner:{partner.id}"
        if document_key:
            return f"document:{document_key}"
        return False

    @staticmethod
    def _appropriation(line):
        detail = line.value_detail if isinstance(line.value_detail, dict) else {}
        appropriation = detail.get("apropriacao") or {}
        if not isinstance(appropriation, dict):
            return {}
        return appropriation

    @staticmethod
    def _tax_id(value):
        return "".join(char for char in (value or "") if char.isalnum()).upper()

    @staticmethod
    def _number(value):
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0
