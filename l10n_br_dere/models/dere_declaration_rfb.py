# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.tools import float_is_zero, float_round

from ..constants import (
    EVENT_D1011,
    EVENT_D1101,
    EVENT_D1106,
    EVENT_D1121,
    EVENT_D1199,
    RETURN_D9101,
    RETURN_D9106,
    RETURN_D9199,
)

RFB_RETURN_EVENTS = (EVENT_D1101, EVENT_D1106, EVENT_D1121, EVENT_D1199)
RFB_TAX_TEXT_FIELDS = frozenset({"codBC", "xDetBC", "memoriaCalculo"})
RECEIPT_SEPARATOR = ", "


def _amount(value):
    return float(value) if value else 0.0


def _rounded(value):
    return float_round(abs(value or 0.0), precision_digits=2)


class DereDeclaration(models.Model):
    _name = "l10n_br_dere.declaration"
    _inherit = ["l10n_br_dere.declaration", "spec.mixin.dere.currency"]

    tax_assessment_line_ids = fields.One2many(
        comodel_name="l10n_br_dere.tax.assessment.line",
        inverse_name="declaration_id",
        string="RFB tax bases",
    )
    rfb_assessment_event_id = fields.Many2one(
        comodel_name="l10n_br_dere.event",
        string="Assessment return",
        readonly=True,
        copy=False,
        help="Accepted D-1199 whose D-9199 return filled the RFB assessment.",
    )
    rfb_v_is = fields.Monetary(
        string="RFB IS", currency_field="brl_currency_id", readonly=True, copy=False
    )
    rfb_v_ibs_mun = fields.Monetary(
        string="RFB municipal IBS",
        currency_field="brl_currency_id",
        readonly=True,
        copy=False,
    )
    rfb_v_ibs_uf = fields.Monetary(
        string="RFB state IBS",
        currency_field="brl_currency_id",
        readonly=True,
        copy=False,
    )
    rfb_v_ibs_tot = fields.Monetary(
        string="RFB total IBS",
        currency_field="brl_currency_id",
        readonly=True,
        copy=False,
    )
    rfb_v_cbs = fields.Monetary(
        string="RFB CBS", currency_field="brl_currency_id", readonly=True, copy=False
    )
    rfb_nr_recibo_balancete = fields.Char(
        string="Trial balance receipt used", size=31, readonly=True, copy=False
    )
    rfb_nr_recibo_aplic_fin = fields.Char(
        string="Technical-reserve receipt used", size=31, readonly=True, copy=False
    )
    rfb_nr_recibo_rel_dedu = fields.Char(
        string="Deduction receipts used", readonly=True, copy=False
    )
    rfb_total_ids = fields.Many2many(
        comodel_name="l10n_br_dere.event.total",
        compute="_compute_rfb_assessment",
        string="RFB totals",
    )
    rfb_mismatch = fields.Boolean(
        compute="_compute_rfb_assessment",
        string="RFB mismatch",
        help="The RFB return differs from the local data or used another "
        "receipt than the events in force.",
    )

    @api.depends(
        "state",
        "event_ids.state",
        "event_ids.nr_recibo",
        "event_ids.nr_recibo_pgcc",
        "event_ids.total_ids.has_difference",
        "table_period_id.event_ids.nr_recibo",
        "rfb_assessment_event_id",
        "rfb_nr_recibo_balancete",
        "rfb_nr_recibo_aplic_fin",
        "rfb_nr_recibo_rel_dedu",
    )
    def _compute_rfb_assessment(self):
        for rec in self:
            events = rec._rfb_return_events()
            rec.rfb_total_ids = events.total_ids
            rec.rfb_mismatch = bool(
                rec._rfb_issues(events) or rec._rfb_closing_issues()
            )

    def _rfb_return_events(self):
        self.ensure_one()
        events = self.env["l10n_br_dere.event"]
        for event_type in RFB_RETURN_EVENTS:
            events |= self._active_event(event_type)
        return events

    def _rfb_issues(self, events):
        self.ensure_one()
        pgcc_receipt = self._active_event(EVENT_D1011).nr_recibo
        issues = []
        for event in events:
            used = event.nr_recibo_pgcc
            if used and pgcc_receipt and used != pgcc_receipt:
                issues.append(
                    _(
                        "%(event)s was totalized with PGCC receipt %(used)s "
                        "instead of the D-1011 receipt in force %(active)s."
                    )
                    % {
                        "event": event.event_type,
                        "used": used,
                        "active": pgcc_receipt,
                    }
                )
            for total in event.total_ids.filtered("has_difference"):
                issues.append(
                    _("%(event)s total %(code)s: RFB %(rfb).2f, " "local %(local).2f.")
                    % {
                        "event": event.event_type,
                        "code": total.dere12_codTrib or "",
                        "rfb": total.dere12_vApurTot,
                        "local": total.local_v_apur,
                    }
                )
        return issues

    def _rfb_closing_issues(self):
        """Compare the receipts used by D-9199 with the events in force.

        A reopened period keeps the previous assessment for reference, so
        its receipts are not compared until the next closing is accepted.
        """
        self.ensure_one()
        if not self.rfb_assessment_event_id or self.state == "reopened":
            return []
        issues = []
        pairs = (
            (
                EVENT_D1101,
                self.rfb_nr_recibo_balancete,
                self._active_event(EVENT_D1101).nr_recibo,
            ),
            (
                EVENT_D1106,
                self.rfb_nr_recibo_aplic_fin,
                self._active_event(EVENT_D1106).nr_recibo,
            ),
        )
        for event_type, used, active in pairs:
            if (used or active) and used != active:
                issues.append(
                    _(
                        "The closing used %(event)s receipt %(used)s instead "
                        "of %(active)s."
                    )
                    % {
                        "event": event_type,
                        "used": used or "-",
                        "active": active or "-",
                    }
                )
        deduction = self._active_event(EVENT_D1121).nr_recibo
        used_deductions = (self.rfb_nr_recibo_rel_dedu or "").split(RECEIPT_SEPARATOR)
        if deduction and deduction not in used_deductions:
            issues.append(
                _("The closing did not use the D-1121 receipt %(receipt)s.")
                % {"receipt": deduction}
            )
        return issues

    def _tax_assessment_line_vals(self, event, line):
        self.ensure_one()
        vals = {
            "declaration_id": self.id,
            "event_id": event.id,
            "regime": line.get("regime"),
        }
        for key, value in line.items():
            if key == "regime":
                continue
            vals[f"dere12_{key}"] = (
                value or False if key in RFB_TAX_TEXT_FIELDS else _amount(value)
            )
        return vals

    def _store_rfb_assessment(self, event, payload):
        self.ensure_one()
        taxes = payload.get("taxes") or {}
        receipts = payload.get("receipts") or {}
        total = taxes.get("total") or {}
        self.tax_assessment_line_ids.sudo().unlink()
        self.env["l10n_br_dere.tax.assessment.line"].sudo().create(
            [
                self._tax_assessment_line_vals(event, line)
                for line in taxes.get("lines") or []
            ]
        )
        self.write(
            {
                "rfb_assessment_event_id": event.id,
                "rfb_v_is": _amount(total.get("vIS")),
                "rfb_v_ibs_mun": _amount(total.get("vIBSMun")),
                "rfb_v_ibs_uf": _amount(total.get("vIBSUF")),
                "rfb_v_ibs_tot": _amount(total.get("vIBSTot")),
                "rfb_v_cbs": _amount(total.get("vCBS")),
                "rfb_nr_recibo_balancete": receipts.get("nrReciboBalancete") or False,
                "rfb_nr_recibo_aplic_fin": receipts.get("nrReciboAplicFin") or False,
                "rfb_nr_recibo_rel_dedu": RECEIPT_SEPARATOR.join(
                    receipts.get("nrReciboRelDedu") or []
                )
                or False,
            }
        )

    def _local_rfb_totals(self, event_type):
        self.ensure_one()
        if event_type == EVENT_D1106:
            amount = sum(_rounded(line.dere12_vApur) for line in self.reserve_line_ids)
            return {(False, False): amount}
        totals = defaultdict(float)
        for line in self.trial_line_ids:
            account = line.pgcc_account_id
            key = (account.tax_code_id.code or False, account.dere12_indTribISS or "0")
            totals[key] += _rounded(line.dere12_vApur)
        return dict(totals)

    def _store_rfb_totals(self, event, totals):
        self.ensure_one()
        event.sudo().total_ids.unlink()
        local = self._local_rfb_totals(event.event_type)
        rows = []
        for item in totals:
            key = (item.get("codTrib") or False, item.get("indTribISS") or False)
            rows.append(
                {
                    "event_id": event.id,
                    "dere12_codTrib": key[0],
                    "dere12_indTribISS": key[1],
                    "dere12_vApurTot": _amount(item.get("vApurTot")),
                    "dere12_vTotSaldoInic": _amount(item.get("vTotSaldoInic")),
                    "dere12_vTotSaldoFinal": _amount(item.get("vTotSaldoFinal")),
                    "local_v_apur": local.pop(key, 0.0),
                }
            )
        rows += [
            {
                "event_id": event.id,
                "dere12_codTrib": code,
                "dere12_indTribISS": ind_trib_iss,
                "dere12_vApurTot": 0.0,
                "local_v_apur": amount,
            }
            for (code, ind_trib_iss), amount in local.items()
            if not float_is_zero(amount, precision_digits=2)
        ]
        return self.env["l10n_br_dere.event.total"].sudo().create(rows)

    def _apply_return_content(self, event, payload):
        res = super()._apply_return_content(event, payload)
        if event.state != "accepted" or not payload:
            return res
        if event.return_type in (RETURN_D9101, RETURN_D9106):
            self._store_rfb_totals(event, payload.get("totals") or [])
        issues = self._rfb_issues(event)
        if event.return_type == RETURN_D9199:
            self._store_rfb_assessment(event, payload)
            issues += self._rfb_closing_issues()
        if issues:
            self.message_post(
                body=Markup("%s<br/>%s")
                % (
                    _("The RFB return differs from the local data:"),
                    Markup("<br/>").join(issues),
                )
            )
        return res
