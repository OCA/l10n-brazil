# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import timedelta
from itertools import combinations

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import SQL

from ..constants import (
    ACTIVE_STATES,
    ALERT_ASSIGNMENT,
    ALERT_DUPLICATE,
    ALERT_NO_TITLE,
    ALERT_UNKNOWN_PARTNER,
    ALLOCATION_MODEL,
    DEBIT_MODEL,
    IDENTITY_ASSIGNMENT,
    IDENTITY_FULL,
    IDENTITY_ROOT,
    MATCH_MODEL,
    MAX_MULTI_PARCELS,
    MAX_MULTI_POOL,
    MIN_SCORE,
    OPEN_STATES,
    SCORE_AMOUNT_EQUAL,
    SCORE_AMOUNT_TOLERANCE,
    SCORE_DUE_EQUAL,
    SCORE_DUE_WINDOW,
    SCORE_IDENTITY_FULL,
    SCORE_IDENTITY_PARTIAL,
    SCORE_NUMBER_EQUAL,
    SOURCE_MODEL,
    SOURCE_TYPES,
    STATES,
    STATUS_CANCELLED,
    STATUS_OPEN,
    STATUS_PAID,
    STATUS_REFUSED,
    STATUS_WRITTEN_OFF,
)
from ..utils import (
    cnpj_root,
    format_cnpj,
    normalize_cnpj,
    normalize_digitable_line,
    normalize_document_number,
    to_date,
)

_logger = logging.getLogger(__name__)

RECOMMENDED_ACTIONS = [
    ("link", "Link"),
    ("link_many", "Link installments"),
    ("create_bill", "Create bill"),
    ("review", "Review"),
    ("verify", "Verify"),
    ("add_to_payment", "Add to payment order"),
    ("none", "None"),
]

# Fields a source may fill, in the names of the Odoo model.
UPSERT_FIELDS = (
    "payer_cnpj",
    "digitable_line",
    "barcode",
    "beneficiary_vat",
    "beneficiary_name",
    "beneficiary_trade_name",
    "guarantor_vat",
    "guarantor_name",
    "issuer_bank",
    "document_number",
    "amount",
    "discount_amount",
    "interest_amount",
    "fine_amount",
    "date_due",
    "date_limit",
    "raw_payload",
)
CNPJ_FIELDS = ("payer_cnpj", "beneficiary_vat", "guarantor_vat")
MONEY_FIELDS = ("amount", "discount_amount", "interest_amount", "fine_amount")
DATE_FIELDS = ("date_due", "date_limit")
MAX_UNDO_STACK = 5


class DdaDebit(models.Model):
    _name = DEBIT_MODEL
    _description = "DDA boleto"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_due, id"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, readonly=True
    )
    payer_cnpj = fields.Char(string="Payer CNPJ", required=True, index=True)
    digitable_line = fields.Char(required=True, index=True)
    barcode = fields.Char()
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Vendor",
        index=True,
        help="Vendor identified by the CNPJ of the beneficiary or of the guarantor.",
    )
    beneficiary_vat = fields.Char(string="Beneficiary CNPJ")
    beneficiary_name = fields.Char()
    beneficiary_trade_name = fields.Char()
    guarantor_vat = fields.Char(string="Guarantor CNPJ")
    guarantor_name = fields.Char()
    issuer_bank = fields.Char()
    document_number = fields.Char()
    amount = fields.Monetary(currency_field="currency_id", required=True)
    discount_amount = fields.Monetary(currency_field="currency_id")
    interest_amount = fields.Monetary(currency_field="currency_id")
    fine_amount = fields.Monetary(currency_field="currency_id")
    date_due = fields.Date(index=True)
    date_limit = fields.Date()
    state = fields.Selection(
        selection=STATES,
        default="new",
        required=True,
        index=True,
        tracking=True,
        copy=False,
    )
    ignore_reason = fields.Char(copy=False)
    verified_by_id = fields.Many2one(comodel_name="res.users", copy=False)
    verified_date = fields.Datetime(copy=False)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned to",
        tracking=True,
        copy=False,
    )
    source_ids = fields.One2many(
        comodel_name=SOURCE_MODEL, inverse_name="debit_id", string="Sources"
    )
    allocation_ids = fields.One2many(
        comodel_name=ALLOCATION_MODEL, inverse_name="debit_id", string="Allocations"
    )
    match_ids = fields.One2many(
        comodel_name=MATCH_MODEL, inverse_name="debit_id", string="Suggestions"
    )
    alert_codes = fields.Char(copy=False)
    is_suspect = fields.Boolean(
        compute="_compute_is_suspect",
        store=True,
        help="No title and an unknown vendor (or a possible duplicate): blocked for "
        "payment until somebody records the verification.",
    )
    divergence_amount = fields.Monetary(
        currency_field="currency_id",
        copy=False,
        help="Boleto amount minus the open amount of the title (suggested or "
        "linked). Nothing edits the invoice: the difference goes to the write-off.",
    )
    recommended_action = fields.Selection(
        selection=RECOMMENDED_ACTIONS, compute="_compute_recommended"
    )
    recommended_label = fields.Char(compute="_compute_recommended")
    recommended_move_line_id = fields.Many2one(
        comodel_name="account.move.line", compute="_compute_recommended"
    )
    suggestion_label = fields.Char(compute="_compute_suggestion_label")
    alert_unknown_partner = fields.Boolean(compute="_compute_alert_flags")
    alert_no_title = fields.Boolean(compute="_compute_alert_flags")
    alert_duplicate = fields.Boolean(compute="_compute_alert_flags")
    alert_assignment = fields.Boolean(compute="_compute_alert_flags")
    alert_labels = fields.Char(string="Alerts", compute="_compute_alert_flags")
    days_to_due = fields.Integer(compute="_compute_days_to_due")
    # Masked copies for the screen; the raw fields stay for search and filters.
    payer_cnpj_display = fields.Char(
        string="Payer CNPJ (masked)", compute="_compute_cnpj_display"
    )
    beneficiary_vat_display = fields.Char(
        string="Beneficiary CNPJ (masked)", compute="_compute_cnpj_display"
    )
    guarantor_vat_display = fields.Char(
        string="Guarantor CNPJ (masked)", compute="_compute_cnpj_display"
    )
    link_mode = fields.Selection(
        selection=[("auto", "Automatic rule"), ("manual", "Manual")], copy=False
    )
    linked_by_id = fields.Many2one(comodel_name="res.users", copy=False)
    payment_order_id = fields.Many2one(
        comodel_name="account.payment.order", copy=False, ondelete="set null"
    )
    bill_id = fields.Many2one(
        comodel_name="account.move",
        string="Created bill",
        copy=False,
        ondelete="set null",
    )
    bank_updated_at = fields.Datetime(copy=False)
    last_action = fields.Char(copy=False)
    undo_stack = fields.Text(copy=False)
    raw_payload = fields.Text(
        copy=False,
        groups="l10n_br_dda.group_dda_manager",
        help="Answer of the source, already masked.",
    )

    _sql_constraints = [
        (
            "unique_boleto",
            "unique(company_id, payer_cnpj, digitable_line)",
            "This boleto already exists for the payer.",
        )
    ]

    # === NORMALIZATION ON EVERY WRITE PATH === #
    @api.model
    def _dda_normalize_vals(self, vals):
        vals = dict(vals)
        for name in CNPJ_FIELDS:
            if name in vals:
                vals[name] = normalize_cnpj(vals[name]) or False
        for name in ("digitable_line", "barcode"):
            if name in vals:
                vals[name] = normalize_digitable_line(vals[name]) or False
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._dda_normalize_vals(vals) for vals in vals_list]
        return super().create(vals_list)

    def write(self, vals):
        return super().write(self._dda_normalize_vals(vals))

    # === COMPUTES === #
    @api.depends("beneficiary_name", "partner_id", "amount", "document_number")
    def _compute_display_name(self):
        for debit in self:
            name = debit.beneficiary_name or debit.partner_id.name or _("Boleto")
            number = debit.document_number
            debit.display_name = f"{name} {number}" if number else name

    @api.depends("alert_codes", "verified_date")
    def _compute_is_suspect(self):
        for debit in self:
            codes = set((debit.alert_codes or "").split(","))
            blocked = ALERT_NO_TITLE in codes and (
                ALERT_UNKNOWN_PARTNER in codes or ALERT_DUPLICATE in codes
            )
            debit.is_suspect = bool(blocked and not debit.verified_date)

    @api.depends("alert_codes")
    def _compute_alert_flags(self):
        for debit in self:
            codes = set((debit.alert_codes or "").split(","))
            debit.alert_unknown_partner = ALERT_UNKNOWN_PARTNER in codes
            debit.alert_no_title = ALERT_NO_TITLE in codes
            debit.alert_duplicate = ALERT_DUPLICATE in codes
            debit.alert_assignment = ALERT_ASSIGNMENT in codes
            # the list speaks the language of accounts payable, not the codes
            labels = {
                ALERT_UNKNOWN_PARTNER: _("Unknown vendor"),
                ALERT_NO_TITLE: _("No matching bill"),
                ALERT_DUPLICATE: _("Possible duplicate"),
                ALERT_ASSIGNMENT: _("Assignment: check the assignee"),
            }
            debit.alert_labels = (
                ", ".join(labels[c] for c in labels if c in codes) or False
            )

    @api.depends("payer_cnpj", "beneficiary_vat", "guarantor_vat")
    def _compute_cnpj_display(self):
        for debit in self:
            debit.payer_cnpj_display = format_cnpj(debit.payer_cnpj) or False
            debit.beneficiary_vat_display = format_cnpj(debit.beneficiary_vat) or False
            debit.guarantor_vat_display = format_cnpj(debit.guarantor_vat) or False

    def _compute_days_to_due(self):
        today = fields.Date.context_today(self)
        for debit in self:
            debit.days_to_due = (debit.date_due - today).days if debit.date_due else 0

    @api.depends(
        "state",
        "partner_id",
        "bill_id",
        "bill_id.state",
        "payment_order_id",
        "match_ids.score",
        "match_ids.is_strict",
        "match_ids.is_multi",
        "match_ids.move_line_ids",
        "company_id.dda_create_bill_mode",
    )
    def _compute_recommended(self):
        for debit in self:
            action, label, line = "none", "", self.env["account.move.line"]
            if debit.state in ("new", "suggested"):
                strict = debit.match_ids.filtered(
                    lambda m: m.is_strict and not m.is_multi
                )
                top = debit.match_ids[:1]
                if debit.bill_id and debit.bill_id.state == "draft":
                    label = _("Post the draft bill")
                elif len(strict) == 1:
                    action, line = "link", strict.move_line_ids
                    label = _("Link to %s", strict.label)
                elif top and top.is_multi:
                    action, line = "link_many", top.move_line_ids
                    label = _("Link %s installments", len(top.move_line_ids))
                elif top:
                    action = "review"
                    if len(debit.match_ids) > 1:
                        label = _("Review %s candidates", len(debit.match_ids))
                    else:
                        label = _("Review the suggestion")
                elif (
                    debit.partner_id
                    and debit.company_id.dda_create_bill_mode == "draft"
                ):
                    action, label = "create_bill", _("Create draft bill")
                else:
                    action, label = "review", _("Review")
            elif debit.state == "suspect":
                action, label = "verify", _("Verify vendor")
            elif debit.state == "linked" and not debit.payment_order_id:
                action, label = "add_to_payment", _("Add to payment order")
            debit.recommended_action = action
            debit.recommended_label = label
            debit.recommended_move_line_id = line[:1]

    @api.depends("match_ids", "state", "allocation_ids")
    def _compute_suggestion_label(self):
        for debit in self:
            if debit.allocation_ids and debit.state in ACTIVE_STATES + ("paid",):
                names = debit.allocation_ids.move_line_id.mapped(
                    lambda line: line.document_number or line.move_id.name or ""
                )
                debit.suggestion_label = ", ".join(n for n in names if n)
            elif len(debit.match_ids) > 1:
                debit.suggestion_label = _("%s candidates", len(debit.match_ids))
            elif debit.match_ids:
                debit.suggestion_label = debit.match_ids.label
            else:
                debit.suggestion_label = _("No title")

    # === CHATTER AND UNDO STACK HELPERS === #
    def _dda_note(self, body):
        for debit in self:
            debit.message_post(body=body, subtype_xmlid="mail.mt_note")

    def _dda_push_undo(self, action, data=None):
        self.ensure_one()
        stack = json.loads(self.undo_stack or "[]")
        stack.append({"action": action, "data": data or {}})
        stack = stack[-MAX_UNDO_STACK:]
        self.write({"undo_stack": json.dumps(stack), "last_action": action})

    def _dda_pop_undo(self):
        self.ensure_one()
        stack = json.loads(self.undo_stack or "[]")
        item = stack.pop() if stack else None
        self.write(
            {
                "undo_stack": json.dumps(stack) if stack else False,
                "last_action": stack[-1]["action"] if stack else False,
            }
        )
        return item

    def _dda_check_group(self, xmlid):
        if not self.env.user.has_group(xmlid) and not self.env.su:
            raise AccessError(_("You are not allowed to do this action."))

    # === UPSERT (PUBLIC API FOR THE GLUE MODULES AND THE CNAB IMPORT) === #
    @api.model
    def _dda_company_by_cnpj(self):
        result = {}
        for company in self.env["res.company"].sudo().search([]):
            cnpj = normalize_cnpj(company.partner_id.vat)
            if cnpj and cnpj not in result:
                result[cnpj] = company
        return result

    @api.model
    def _dda_clean_upsert_vals(self, raw):
        vals = {key: raw[key] for key in UPSERT_FIELDS if key in raw}
        vals = self._dda_normalize_vals(vals)
        for name in MONEY_FIELDS:
            if vals.get(name) is not None and vals.get(name) is not False:
                vals[name] = float(vals[name])
        for name in DATE_FIELDS:
            if name in vals:
                vals[name] = to_date(vals[name])
        if vals.get("raw_payload") and not isinstance(vals["raw_payload"], str):
            vals["raw_payload"] = json.dumps(vals["raw_payload"], default=str)
        return vals

    @api.model
    def _dda_to_utc_naive(self, value):
        value = fields.Datetime.to_datetime(value) if value else None
        if value and value.tzinfo:
            value = value.astimezone(tz=None).replace(tzinfo=None)
        return value

    @api.model
    def _dda_touch_source(self, debit, source_type, source_key, external_id):
        Source = self.env[SOURCE_MODEL].sudo()
        source = Source.search(
            [
                ("debit_id", "=", debit.id),
                ("source_type", "=", source_type),
                ("source_key", "=", source_key),
            ],
            limit=1,
        )
        values = {"last_seen": fields.Datetime.now()}
        if external_id:
            values["external_id"] = str(external_id)
        if source:
            source.write(values)
        else:
            Source.create(
                dict(
                    values,
                    debit_id=debit.id,
                    source_type=source_type,
                    source_key=source_key,
                )
            )

    @api.model
    def _dda_upsert(self, vals_list, source_type, source_key):
        """Create or update boletos of a source, idempotently."""
        debit_sudo = self.sudo()
        company_by_cnpj = debit_sudo._dda_company_by_cnpj()
        touched = debit_sudo.browse()
        for raw in vals_list:
            vals = debit_sudo._dda_clean_upsert_vals(raw)
            payer, line = vals.get("payer_cnpj"), vals.get("digitable_line")
            company = company_by_cnpj.get(payer or "")
            if not payer or not line or not company:
                _logger.warning(
                    "DDA boleto skipped: no company for the payer CNPJ or no "
                    "digitable line (source %s)",
                    source_key,
                )
                continue
            updated_at = debit_sudo._dda_to_utc_naive(raw.get("updated_at"))
            debit = debit_sudo.search(
                [
                    ("company_id", "=", company.id),
                    ("payer_cnpj", "=", payer),
                    ("digitable_line", "=", line),
                ],
                limit=1,
            )
            stale = False
            if debit:
                stale = bool(
                    updated_at
                    and debit.bank_updated_at
                    and updated_at < debit.bank_updated_at
                )
                if not stale:
                    changes = {
                        key: value
                        for key, value in vals.items()
                        if value not in (None, False, "")
                        and key not in ("payer_cnpj", "digitable_line")
                    }
                    if updated_at:
                        changes["bank_updated_at"] = updated_at
                    debit.write(changes)
            else:
                if not vals.get("amount") or vals["amount"] <= 0:
                    _logger.warning("DDA boleto skipped: no amount (%s)", source_key)
                    continue
                create_vals = {
                    key: value
                    for key, value in vals.items()
                    if value not in (None, False, "")
                }
                create_vals.update(
                    company_id=company.id, bank_updated_at=updated_at or False
                )
                debit = debit_sudo.with_context(tracking_disable=False).create(
                    create_vals
                )
                debit._dda_note(
                    _("Captured from %(type)s (%(key)s).")
                    % {
                        "type": dict(SOURCE_TYPES).get(source_type, source_type),
                        "key": source_key,
                    }
                )
            debit_sudo._dda_touch_source(
                debit, source_type, source_key, raw.get("external_id")
            )
            if not stale:
                debit._dda_apply_status(raw.get("status") or STATUS_OPEN)
            touched |= debit
        touched._dda_run_matching()
        return self.browse(touched.ids)

    def _dda_apply_status(self, status):
        self.ensure_one()
        status = (status or STATUS_OPEN).upper()
        if status == STATUS_PAID:
            if self.state in ("paid", "paid_elsewhere"):
                return
            if self.payment_order_id or self.state == "in_payment":
                self._dda_note(
                    _(
                        "The bank reports this boleto as paid. The accounting "
                        "entry comes from the payment return or the bank statement."
                    )
                )
                return
            self.state = "paid_elsewhere"
            self._dda_note(
                _(
                    "The bank reports this boleto as paid and it is not in a payment "
                    "order of Odoo. Nothing was posted."
                )
            )
        elif status in (STATUS_CANCELLED, STATUS_WRITTEN_OFF):
            if self.state == "cancelled":
                return
            self.state = "cancelled"
            message = _(
                "The beneficiary cancelled or wrote off the DDA boleto %s. "
                "Do not pay it."
            ) % (self.digitable_line,)
            self._dda_note(message)
            for move in self.allocation_ids.move_id:
                move.message_post(body=message, subtype_xmlid="mail.mt_note")
            if self.payment_order_id and hasattr(self.payment_order_id, "message_post"):
                self.payment_order_id.message_post(
                    body=message, subtype_xmlid="mail.mt_note"
                )
        elif status == STATUS_REFUSED:
            if self.state != "ignored":
                self.write(
                    {
                        "state": "ignored",
                        "ignore_reason": _("Refused at the bank (DDA)."),
                    }
                )
        elif self.state in ("cancelled", "paid_elsewhere", "expired"):
            self.state = "new"
            self._dda_note(_("The source reports this boleto as open again."))

    # === MATCHING === #
    def _dda_partner_ids_by_vat(self, vat, root=False):
        vat = normalize_cnpj(vat)
        if not vat:
            return []
        self.env["res.partner"].flush_model(["cnpj_cpf_stripped", "active"])
        operator, param = ("LIKE", vat + "%") if root else ("=", vat)
        self.env.cr.execute(
            SQL(
                """
            SELECT id FROM res_partner
             WHERE active AND cnpj_cpf_stripped IS NOT NULL
               AND regexp_replace(upper(cnpj_cpf_stripped), '[^0-9A-Z]', '', 'g') %s %s
            """,
                SQL(operator),
                param,
            )
        )
        return [row[0] for row in self.env.cr.fetchall()]

    def _dda_resolve_identity(self):
        """Return (identity map by commercial partner id, partner of the boleto)."""
        self.ensure_one()
        partner_model = self.env["res.partner"].sudo()
        identity = {}

        def put(partners, score, kind):
            for partner in partners.commercial_partner_id:
                current = identity.get(partner.id)
                if not current or current[0] < score:
                    identity[partner.id] = (score, kind)

        beneficiary = partner_model.browse(
            self._dda_partner_ids_by_vat(self.beneficiary_vat)
        )
        guarantor = partner_model.browse(
            self._dda_partner_ids_by_vat(self.guarantor_vat)
        )
        put(beneficiary, SCORE_IDENTITY_FULL, IDENTITY_FULL)
        put(guarantor, SCORE_IDENTITY_PARTIAL, IDENTITY_ASSIGNMENT)
        if beneficiary:
            assigned = partner_model.search(
                [("dda_assignee_ids", "in", beneficiary.ids)]
            )
            put(assigned, SCORE_IDENTITY_PARTIAL, IDENTITY_ASSIGNMENT)
        root = cnpj_root(self.beneficiary_vat)
        if root:
            siblings = partner_model.browse(
                self._dda_partner_ids_by_vat(root, root=True)
            )
            put(siblings, SCORE_IDENTITY_PARTIAL, IDENTITY_ROOT)
        partner = (beneficiary or guarantor)[:1]
        return identity, partner

    def _dda_candidate_lines(self, identity):
        line_model = self.env["account.move.line"].sudo()
        if not identity:
            return line_model
        partners = (
            self.env["res.partner"]
            .sudo()
            .with_context(active_test=False)
            .search([("commercial_partner_id", "in", list(identity))])
        )
        lines = line_model.search(
            [
                ("company_id", "=", self.company_id.id),
                ("parent_state", "=", "posted"),
                ("account_id.account_type", "=", "liability_payable"),
                ("reconciled", "=", False),
                ("amount_residual", "<", 0),
                ("partner_id", "in", partners.ids),
            ],
            order="date_maturity, id",
            limit=200,
        )
        if not lines:
            return lines
        busy = (
            self.env[ALLOCATION_MODEL]
            .sudo()
            .search(
                [
                    ("move_line_id", "in", lines.ids),
                    ("debit_id", "!=", self.id),
                    ("debit_id.state", "in", ACTIVE_STATES),
                ]
            )
            .move_line_id
        )
        return lines.filtered(
            lambda line: line not in busy
            and not any(
                payline.order_id.state != "cancel"
                for payline in getattr(line, "payment_line_ids", [])
            )
        )

    def _dda_evaluate(self, lines, identity_score, kind):
        """Score one candidate (one line, or several installments)."""
        self.ensure_one()
        company = self.company_id
        currency = company.currency_id
        total = sum(-line.amount_residual for line in lines)
        diff = self.amount - total
        score = identity_score
        evidence = []
        if kind == IDENTITY_FULL:
            evidence.append(_("Same CNPJ"))
        elif kind == IDENTITY_ASSIGNMENT:
            evidence.append(_("Assignment: the boleto is not issued by the vendor"))
        else:
            evidence.append(_("Same CNPJ root, another establishment"))
        amount_equal = currency.is_zero(diff)
        tolerance = company.dda_amount_tolerance
        if amount_equal:
            score += SCORE_AMOUNT_EQUAL
            evidence.append(_("Same amount"))
        elif tolerance and abs(diff) <= tolerance:
            score += SCORE_AMOUNT_TOLERANCE
            evidence.append(_("Amount within the tolerance (difference %s)", diff))
        else:
            evidence.append(_("Amount differs by %s", diff))
        date_diff = -1
        if self.date_due and all(line.date_maturity for line in lines):
            date_diff = max(
                abs((line.date_maturity - self.date_due).days) for line in lines
            )
            if date_diff == 0:
                score += SCORE_DUE_EQUAL
                evidence.append(_("Same due date"))
            elif date_diff <= company.dda_date_tolerance:
                score += SCORE_DUE_WINDOW
                evidence.append(_("Due date %s days apart", date_diff))
            else:
                evidence.append(
                    _("Due date %s days apart (outside the tolerance)", date_diff)
                )
        conflict = False
        if len(lines) == 1:
            boleto_number = normalize_document_number(self.document_number)
            line_number = normalize_document_number(lines.document_number)
            if boleto_number and line_number:
                if boleto_number == line_number:
                    score += SCORE_NUMBER_EQUAL
                    evidence.append(_("Same document number"))
                else:
                    conflict = True
                    evidence.append(_("Different document number"))
        strict = (
            len(lines) == 1
            and kind == IDENTITY_FULL
            and amount_equal
            and date_diff == 0
            and not conflict
        )
        return {
            "score": score,
            "evidence": "\n".join(evidence),
            "is_strict": strict,
            "amount_total": total,
            "amount_diff": diff,
            "date_diff": date_diff,
            "identity_kind": kind,
        }

    def _dda_multi_candidates(self, lines, identity):
        """N:1 suggestions: up to 5 installments of the same vendor whose sum is
        the amount of the boleto, all inside the due date window."""
        self.ensure_one()
        window = self.company_id.dda_date_tolerance
        found = []
        by_partner = {}
        for line in lines:
            by_partner.setdefault(line.partner_id.commercial_partner_id.id, []).append(
                line
            )
        for partner_id, partner_lines in by_partner.items():
            pool = [
                line
                for line in partner_lines
                if not self.date_due
                or not line.date_maturity
                or abs((line.date_maturity - self.date_due).days) <= window
            ]
            if self.date_due:
                pool.sort(
                    key=lambda line: (
                        abs((line.date_maturity - self.date_due).days)
                        if line.date_maturity
                        else 9999
                    )
                )
            pool = pool[:MAX_MULTI_POOL]
            target = round(self.amount * 100)
            for size in range(2, min(MAX_MULTI_PARCELS, len(pool)) + 1):
                for combo in combinations(pool, size):
                    cents = sum(round(-line.amount_residual * 100) for line in combo)
                    if cents == target:
                        found.append((partner_id, combo))
                if found:
                    break
        return found

    def _dda_match_one(self):
        self.ensure_one()
        match_model = self.env[MATCH_MODEL].sudo()
        identity, partner = self._dda_resolve_identity()
        lines = self._dda_candidate_lines(identity)
        entries = []
        currency = self.company_id.currency_id
        single_equal = False
        for line in lines:
            score, kind = identity[line.partner_id.commercial_partner_id.id]
            data = self._dda_evaluate(line, score, kind)
            if data["score"] >= MIN_SCORE:
                entries.append(dict(data, lines=line, is_multi=False))
                if currency.is_zero(data["amount_diff"]):
                    single_equal = True
        if not single_equal:
            for partner_id, combo in self._dda_multi_candidates(lines, identity):
                score, kind = identity[partner_id]
                recordset = (
                    self.env["account.move.line"]
                    .sudo()
                    .browse([line.id for line in combo])
                )
                data = self._dda_evaluate(recordset, score, kind)
                if data["score"] >= MIN_SCORE:
                    entries.append(dict(data, lines=recordset, is_multi=True))
        entries.sort(key=lambda entry: -entry["score"])
        self.match_ids.sudo().unlink()
        match_model.create(
            [
                {
                    "debit_id": self.id,
                    "move_line_ids": [(6, 0, entry["lines"].ids)],
                    "is_multi": entry["is_multi"],
                    "score": entry["score"],
                    "identity_kind": entry["identity_kind"],
                    "is_strict": entry["is_strict"],
                    "amount_total": entry["amount_total"],
                    "amount_diff": entry["amount_diff"],
                    "date_diff": entry["date_diff"],
                    "evidence": entry["evidence"],
                }
                for entry in entries
            ]
        )
        self._dda_update_alerts(partner, bool(entries))
        best = entries[0] if entries else None
        self.write(
            {
                "partner_id": partner.id or False,
                "divergence_amount": best["amount_diff"] if best else 0.0,
            }
        )
        return best

    def _dda_update_alerts(self, partner, has_match):
        self.ensure_one()
        codes = []
        if not partner:
            codes.append(ALERT_UNKNOWN_PARTNER)
        if not has_match:
            codes.append(ALERT_NO_TITLE)
        if self.beneficiary_vat:
            duplicates = self.sudo().search_count(
                [
                    ("company_id", "=", self.company_id.id),
                    ("id", "!=", self.id),
                    ("digitable_line", "!=", self.digitable_line),
                    ("beneficiary_vat", "=", self.beneficiary_vat),
                    ("amount", "=", self.amount),
                    ("date_due", "=", self.date_due),
                    ("state", "not in", ("cancelled", "ignored", "expired")),
                ]
            )
            if duplicates:
                codes.append(ALERT_DUPLICATE)
        if self.guarantor_vat and self.guarantor_vat != self.beneficiary_vat:
            codes.append(ALERT_ASSIGNMENT)
        elif self.beneficiary_vat:
            # BTG sends no guarantor: an issuer that is the supplier assignee counts.
            issuers = self._dda_partner_ids_by_vat(self.beneficiary_vat)
            if issuers and self.env["res.partner"].sudo().search_count(
                [("dda_assignee_ids", "in", issuers)]
            ):
                codes.append(ALERT_ASSIGNMENT)
        self.alert_codes = ",".join(codes) or False

    def _dda_run_matching(self):
        """Suggestions, alerts and, when the company allows it, the strict link."""
        debits = self.filtered(
            lambda d: d.state in OPEN_STATES
            and not (d.bill_id and d.bill_id.state == "draft")
        )
        for debit in debits:
            debit._dda_match_one()
            if debit.is_suspect:
                new_state = "suspect"
            elif debit.match_ids:
                new_state = "suggested"
            else:
                new_state = "new"
            if debit.state != new_state:
                debit.state = new_state
        for debit in debits:
            debit._dda_try_auto_link()
        return True

    def _dda_try_auto_link(self):
        self.ensure_one()
        if (
            not self.company_id.dda_auto_link
            or self.state not in ("new", "suggested")
            or self.is_suspect
        ):
            return False
        strict = self.match_ids.filtered(lambda m: m.is_strict and not m.is_multi)
        if len(strict) != 1:
            return False
        rivals = (
            self.env[MATCH_MODEL]
            .sudo()
            .search_count(
                [
                    ("move_line_ids", "in", strict.move_line_ids.ids),
                    ("is_strict", "=", True),
                    ("debit_id", "!=", self.id),
                    ("debit_id.state", "in", ("new", "suggested")),
                ]
            )
        )
        if rivals:
            return False
        self._dda_link(strict.move_line_ids, mode="auto", evidence=strict.evidence)
        return True

    def _dda_refresh_siblings(self, lines):
        """Other open boletos that listed these lines have to look again."""
        siblings = (
            self.env[MATCH_MODEL]
            .sudo()
            .search([("move_line_ids", "in", lines.ids)])
            .debit_id
            - self
        )
        siblings.filtered(lambda d: d.state in OPEN_STATES)._dda_run_matching()

    # === ACTIONS === #
    def _dda_check_open(self):
        for debit in self:
            if debit.state not in OPEN_STATES:
                raise UserError(
                    _(
                        "The boleto %(name)s is %(state)s: the action is not "
                        "available anymore.",
                        name=debit.display_name,
                        state=dict(STATES).get(debit.state),
                    )
                )

    def _dda_link(
        self,
        lines,
        amounts=None,
        mode="manual",
        evidence=None,
        update_due=False,
        push_undo=True,
    ):
        self.ensure_one()
        self._dda_check_open()
        lines = lines.sudo()
        if not lines:
            raise UserError(_("Select at least one payable line."))
        for line in lines:
            if (
                line.company_id != self.company_id
                or line.account_id.account_type != "liability_payable"
                or line.reconciled
                or line.parent_state != "posted"
            ):
                raise UserError(
                    _(
                        "%s is not an open payable line of the company.",
                        line.display_name,
                    )
                )
        busy = (
            self.env[ALLOCATION_MODEL]
            .sudo()
            .search(
                [
                    ("move_line_id", "in", lines.ids),
                    ("debit_id", "!=", self.id),
                    ("debit_id.state", "in", ACTIVE_STATES),
                ]
            )
        )
        if busy:
            raise UserError(
                _(
                    "%s is already linked to another DDA boleto.",
                    busy[0].move_line_id.display_name,
                )
            )
        amounts = amounts or {}
        allocations = self.env[ALLOCATION_MODEL].sudo()
        for line in lines:
            allocations |= allocations.create(
                {
                    "debit_id": self.id,
                    "move_line_id": line.id,
                    "amount": amounts.get(line.id, -line.amount_residual),
                }
            )
        previous_due = {}
        if update_due and self.date_due:
            for line in lines:
                if line.date_maturity != self.date_due:
                    previous_due[str(line.id)] = fields.Date.to_string(
                        line.date_maturity
                    )
                    line.write({"date_maturity": self.date_due})
                    line.move_id.message_post(
                        body=_(
                            "Due date changed to %(new)s from the DDA boleto "
                            "(it was %(old)s).",
                            new=self.date_due,
                            old=previous_due[str(line.id)],
                        ),
                        subtype_xmlid="mail.mt_note",
                    )
        total = sum(allocations.mapped("amount"))
        who = _("automatic rule") if mode == "auto" else self.env.user.name
        names = ", ".join(
            line.document_number or line.move_id.name or str(line.id) for line in lines
        )
        body = _("Linked to %(names)s by %(who)s.", names=names, who=who)
        if evidence:
            body = Markup("<br/>").join([body, *evidence.split("\n")])
        self.write(
            {
                "state": "linked",
                "link_mode": mode,
                "linked_by_id": False if mode == "auto" else self.env.user.id,
                "divergence_amount": self.amount - total,
            }
        )
        self._dda_note(body)
        if push_undo:
            self._dda_push_undo(
                "link",
                {"allocation_ids": allocations.ids, "previous_due": previous_due},
            )
        self._dda_refresh_siblings(lines)
        return True

    def action_link(self, move_line_ids, amounts=None, update_due=False):
        """Link the boleto to payable lines (one, or several installments)."""
        self.ensure_one()
        lines = self.env["account.move.line"].sudo().browse(list(move_line_ids))
        amounts = {int(k): v for k, v in (amounts or {}).items()}
        if len(lines) > 1:
            total = sum(amounts.get(line.id, -line.amount_residual) for line in lines)
            if not self.company_id.currency_id.is_zero(total - self.amount):
                raise UserError(
                    _(
                        "The installments add up to %(total)s but the boleto is "
                        "%(amount)s.",
                        total=total,
                        amount=self.amount,
                    )
                )
        return self._dda_link(lines, amounts=amounts, update_due=update_due)

    def action_create_bill(self):
        """Vendor bill in draft with the data of the boleto."""
        for debit in self:
            debit._dda_check_open()
            if not debit.partner_id:
                raise UserError(
                    _("Identify the vendor of the boleto before creating the bill.")
                )
            journal = self.env["account.journal"].search(
                [("type", "=", "purchase"), ("company_id", "=", debit.company_id.id)],
                limit=1,
            )
            if not journal:
                raise UserError(_("The company has no purchase journal."))
            bill = (
                self.env["account.move"]
                .with_company(debit.company_id)
                .create(
                    {
                        "move_type": "in_invoice",
                        "company_id": debit.company_id.id,
                        "journal_id": journal.id,
                        "partner_id": debit.partner_id.id,
                        "invoice_date": fields.Date.context_today(debit),
                        "invoice_date_due": debit.date_due or False,
                        "invoice_payment_term_id": False,
                        "ref": debit.document_number or False,
                        "invoice_line_ids": [
                            (
                                0,
                                0,
                                {
                                    "name": _("DDA boleto %s")
                                    % (debit.document_number or debit.digitable_line),
                                    "quantity": 1.0,
                                    "price_unit": debit.amount,
                                },
                            )
                        ],
                    }
                )
            )
            debit.bill_id = bill
            debit._dda_note(
                _("Draft vendor bill %(bill)s created by %(user)s.")
                % {"bill": bill.display_name, "user": self.env.user.name}
            )
            debit._dda_push_undo("create_bill", {"bill_id": bill.id})
        return True

    def action_ignore(self, reason):
        if not reason or not str(reason).strip():
            raise UserError(_("Inform why the boleto is ignored."))
        for debit in self:
            debit._dda_check_open()
            previous = debit.state
            debit.write({"state": "ignored", "ignore_reason": reason})
            debit._dda_note(
                _("Ignored by %(user)s: %(reason)s")
                % {"user": self.env.user.name, "reason": reason}
            )
            debit._dda_push_undo("ignore", {"previous_state": previous})
        return True

    def action_mark_verified(self):
        """Record the verification of a suspect boleto (approvers only)."""
        self._dda_check_group("l10n_br_dda.group_dda_approver")
        for debit in self:
            debit.write(
                {
                    "verified_by_id": self.env.user.id,
                    "verified_date": fields.Datetime.now(),
                }
            )
            debit._dda_note(
                _("Verified by %s: the boleto was confirmed with the vendor.")
                % self.env.user.name
            )
            debit._dda_push_undo("verify", {})
            if debit.state == "suspect":
                debit._dda_run_matching()
        return True

    def _dda_find_payment_order(self):
        self.ensure_one()
        company = self.company_id
        mode = company.dda_payment_mode_id
        if not mode:
            raise UserError(
                _("Set the DDA payment mode in the accounting settings first.")
            )
        order_model = self.env["account.payment.order"].with_company(company)
        order = order_model.search(
            [
                ("company_id", "=", company.id),
                ("payment_mode_id", "=", mode.id),
                ("state", "=", "draft"),
            ],
            limit=1,
            order="id desc",
        )
        if order:
            return order, False
        values = {
            "company_id": company.id,
            "payment_mode_id": mode.id,
            "payment_type": "outbound",
        }
        journal = mode.fixed_journal_id or mode.variable_journal_ids[:1]
        if journal:
            values["journal_id"] = journal.id
        return order_model.create(values), True

    def action_add_to_payment_order(self):
        """Put the linked boletos in the draft payment order of the company."""
        for debit in self:
            if debit.state != "linked":
                raise UserError(
                    _("Only linked boletos go to a payment order (%s).")
                    % debit.display_name
                )
            if debit.is_suspect:
                raise UserError(
                    _(
                        "%s is a suspect boleto: an approver has to record the "
                        "verification before payment."
                    )
                    % debit.display_name
                )
            if debit.payment_order_id:
                raise UserError(_("The boleto is already in a payment order."))
            order, created = debit._dda_find_payment_order()
            first = debit.allocation_ids.sorted("id")[:1].move_line_id
            paylines = first.create_payment_line_from_move_line(order)
            debit.write({"payment_order_id": order.id, "state": "in_payment"})
            extra = ""
            if len(debit.allocation_ids) > 1:
                extra = _(
                    " The boleto settles %s installments: it goes as one payment "
                    "line, on the first one."
                ) % len(debit.allocation_ids)
            debit._dda_note(
                _("Added to the payment order %(order)s by %(user)s.%(extra)s")
                % {
                    "order": order.display_name,
                    "user": self.env.user.name,
                    "extra": extra,
                }
            )
            debit._dda_push_undo(
                "add_to_payment",
                {
                    "order_id": order.id,
                    "created_order": created,
                    "payline_ids": paylines.ids,
                    "line_id": first.id,
                },
            )
        return True

    def _dda_payment_line_vals(self, move_line):
        """Values of the account.payment.line for the allocated line."""
        self.ensure_one()
        first = self.allocation_ids.sorted("id")[:1].move_line_id
        if move_line != first:
            return {}
        currency = self.currency_id
        extra = self.amount - sum(self.allocation_ids.mapped("amount"))
        interest = self.interest_amount + (extra if extra > 0 else 0.0)
        discount = self.discount_amount + (-extra if extra < 0 else 0.0)
        vals = {
            "digitable_line": self.digitable_line,
            "barcode": self.barcode or False,
            "interest_value": currency.round(interest),
            "fee_value": currency.round(self.fine_amount),
            "discount_value": currency.round(discount),
        }
        if len(self.allocation_ids) > 1:
            vals["amount_currency"] = currency.round(
                sum(self.allocation_ids.mapped("amount"))
            )
        return vals

    def action_apply_recommended(self):
        """Apply the recommended action of each boleto; returns a summary."""
        summary = {
            "linked": 0,
            "bills": 0,
            "ignored": 0,
            "skipped": 0,
            "total_amount": 0.0,
        }
        for debit in self:
            action = debit.recommended_action
            try:
                with self.env.cr.savepoint():
                    if action in ("link", "link_many"):
                        lines = (
                            debit.recommended_move_line_id
                            if action == "link"
                            else debit.match_ids[:1].move_line_ids
                        )
                        evidence = debit.match_ids[:1].evidence
                        debit._dda_link(lines, evidence=evidence)
                        summary["linked"] += 1
                    elif action == "create_bill":
                        debit.action_create_bill()
                        summary["bills"] += 1
                    else:
                        summary["skipped"] += 1
                        continue
                    summary["total_amount"] += debit.amount
            except UserError as error:
                summary["skipped"] += 1
                debit._dda_note(_("Not applied: %s") % error.args[0])
        return summary

    def action_apply_recommended_notify(self):
        """Same as action_apply_recommended, answering with a notification."""
        summary = self.action_apply_recommended()
        message = _(
            "%(linked)s links, %(bills)s draft bills, %(skipped)s skipped; "
            "total %(total).2f",
            linked=summary["linked"],
            bills=summary["bills"],
            skipped=summary["skipped"],
            total=summary["total_amount"],
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Recommended actions"),
                "message": message,
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def action_undo(self):
        """Revert the last action of the boleto while it is safe to do so."""
        self.ensure_one()
        stack = json.loads(self.undo_stack or "[]")
        if not stack:
            return False
        item = stack[-1]
        action, data = item["action"], item["data"]
        done = False
        if action == "link":
            done = self._dda_undo_link(data)
        elif action == "ignore":
            if self.state == "ignored":
                self.write({"state": "new", "ignore_reason": False})
                done = True
        elif action == "verify":
            self.write({"verified_by_id": False, "verified_date": False})
            done = True
        elif action == "create_bill":
            bill = self.bill_id
            if bill and bill.state == "draft" and self.state in OPEN_STATES:
                self.bill_id = False
                bill.unlink()
                done = True
            elif not bill:
                done = True
        elif action == "add_to_payment":
            done = self._dda_undo_payment(data)
        if not done:
            self._dda_note(_("Undo is not possible anymore."))
            return False
        self._dda_pop_undo()
        self._dda_note(
            _("%(action)s undone by %(user)s.")
            % {
                "action": action,
                "user": self.env.user.name,
            }
        )
        if self.state in OPEN_STATES:
            self._dda_run_matching()
        return True

    def _dda_undo_link(self, data):
        if self.state != "linked" or self.payment_order_id:
            return False
        allocations = (
            self.env[ALLOCATION_MODEL].sudo().browse(data.get("allocation_ids", []))
        )
        allocations = allocations.exists()
        lines = allocations.move_line_id
        for line_id, old_due in (data.get("previous_due") or {}).items():
            line = self.env["account.move.line"].sudo().browse(int(line_id))
            if line.exists():
                line.write({"date_maturity": old_due})
        allocations.unlink()
        self.write(
            {
                "state": "new",
                "link_mode": False,
                "linked_by_id": False,
                "divergence_amount": 0.0,
            }
        )
        self._dda_refresh_siblings(lines)
        return True

    def _dda_undo_payment(self, data):
        order = self.payment_order_id
        if self.state != "in_payment" or not order or order.state != "draft":
            return False
        paylines = self.env["account.payment.line"].browse(data.get("payline_ids", []))
        line = self.env["account.move.line"].sudo().browse(data.get("line_id"))
        paylines.exists().unlink()
        if line.exists() and line.cnab_state == "added":
            line.cnab_state = "draft"
        self.write({"state": "linked", "payment_order_id": False})
        if data.get("created_order") and not order.payment_line_ids:
            order.unlink()
        return True

    def action_open_match_wizard(self):
        self.ensure_one()
        self._dda_check_open()
        wizard = self.env["l10n_br_dda.match.wizard"].create({"debit_id": self.id})
        wizard._load_candidates()
        return {
            "type": "ir.actions.act_window",
            "name": _("Link boleto"),
            "res_model": "l10n_br_dda.match.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "new",
        }

    def action_open_ignore_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Ignore boletos"),
            "res_model": "l10n_br_dda.ignore.wizard",
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "new",
            "context": {"default_debit_ids": [(6, 0, self.ids)]},
        }

    # === HOOKS FROM THE ACCOUNTING SIDE === #
    @api.model
    def _dda_on_bill_posted(self, moves):
        """A draft bill created from a boleto was posted: link its payable lines."""
        debits = self.sudo().search(
            [("bill_id", "in", moves.ids), ("state", "in", OPEN_STATES)]
        )
        for debit in debits:
            lines = debit.bill_id.line_ids.filtered(
                lambda line: line.account_id.account_type == "liability_payable"
                and not line.reconciled
            )
            if lines:
                debit._dda_link(lines, mode="manual", push_undo=False)
                debit.linked_by_id = debit.create_uid

    @api.model
    def _dda_on_reconcile(self, lines):
        allocations = (
            self.env[ALLOCATION_MODEL]
            .sudo()
            .search(
                [
                    ("move_line_id", "in", lines.ids),
                    ("debit_id.state", "in", ACTIVE_STATES),
                ]
            )
        )
        for debit in allocations.debit_id:
            if all(debit.allocation_ids.move_line_id.mapped("reconciled")):
                debit.state = "paid"
                debit._dda_note(_("The payable line was reconciled: boleto paid."))

    @api.model
    def _dda_settle_installments(self, lines):
        """A boleto paid through its first installment settles the others."""
        allocations = (
            self.env[ALLOCATION_MODEL]
            .sudo()
            .search(
                [
                    ("move_line_id", "in", lines.ids),
                    ("debit_id.state", "=", "in_payment"),
                ]
            )
        )
        for debit in allocations.debit_id:
            first = debit.allocation_ids.sorted("id")[:1].move_line_id
            others = debit.allocation_ids.move_line_id - first
            others = others.filtered(lambda line: not line.reconciled)
            if not first.reconciled or not others:
                continue
            paid = (
                first.matched_debit_ids.debit_move_id
                | first.matched_credit_ids.credit_move_id
            ).filtered(
                lambda line, account=first.account_id: line.account_id == account
                and not line.reconciled
            )
            if paid:
                (paid | others).reconcile()

    @api.model
    def _cron_dda_expire(self):
        today = fields.Date.context_today(self)
        expired = self.sudo().search(
            [("state", "in", OPEN_STATES), ("date_limit", "<", today)]
        )
        for debit in expired:
            debit.state = "expired"
            debit._dda_note(_("The limit date of the boleto has passed."))
        return len(expired)

    # === DASHBOARD AND SOURCES === #
    @api.model
    def _dda_dashboard_domains(self):
        today = fields.Date.context_today(self)
        in_seven = today + timedelta(days=7)
        today_text = fields.Date.to_string(today)
        return {
            "new": [("state", "in", ["new", "suggested"])],
            "due_7": [
                ("state", "in", list(OPEN_STATES) + ["linked"]),
                ("date_due", ">=", today_text),
                ("date_due", "<=", fields.Date.to_string(in_seven)),
            ],
            "divergence": [
                ("state", "in", ["suggested", "linked"]),
                ("divergence_amount", "!=", 0),
            ],
            "suspect": [("state", "=", "suspect")],
            "overdue": [
                ("state", "in", list(OPEN_STATES)),
                ("date_due", "<", today_text),
            ],
        }

    @api.model
    def _dda_source_status(self):
        """Health of each source; the glue modules extend the list."""
        sources = []
        structures = (
            self.env["l10n_br_cnab.structure"]
            .sudo()
            .search_count([("is_dda_return", "=", True), ("state", "=", "approved")])
        )
        last = self.env[SOURCE_MODEL].search(
            [("source_type", "=", "cnab")], order="last_seen desc", limit=1
        )
        if structures or last:
            if not last:
                state, message = "warning", _("No file imported yet.")
            elif last.last_seen < fields.Datetime.now() - timedelta(days=7):
                state, message = "warning", _("The last file is older than 7 days.")
            else:
                state, message = "ok", _("Last file imported.")
            action = False
            try:
                action = self.env["ir.actions.act_window"]._for_xml_id(
                    "l10n_br_dda.action_dda_import_wizard"
                )
            except ValueError:  # pragma: no cover
                action = False
            sources.append(
                {
                    "key": "cnab",
                    "name": _("CNAB file"),
                    "state": state,
                    "last_sync": last.last_seen if last else False,
                    "message": message,
                    "action": action,
                }
            )
        return sources

    @api.model
    def dda_dashboard(self):
        domains = self._dda_dashboard_domains()
        counters = {key: self.search_count(domain) for key, domain in domains.items()}
        currency = self.env.company.currency_id
        return {
            "counters": counters,
            "domains": domains,
            "sources": self._dda_source_status(),
            "currency": {"symbol": currency.symbol, "position": currency.position},
        }
