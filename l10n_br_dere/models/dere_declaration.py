# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar
import json
import re
from collections import defaultdict
from datetime import date

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import (
    FREQ_ENCERR,
    PLANO_CTA_REF,
)

from ..constants import (
    D1199_RECEIPT_RE,
    DEFAULT_VER_APLIC,
    EVENT_D1001,
    EVENT_D1011,
    EVENT_D1101,
    EVENT_D1198,
    EVENT_D1199,
    PERIODIC_EVENTS,
    TABLE_EVENTS,
)
from . import xml_builder


class DereDeclaration(models.Model):
    _name = "l10n_br_dere.declaration"
    _description = "DeRE monthly declaration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "per_apur desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    per_apur = fields.Char(
        string="Assessment period",
        size=7,
        required=True,
        help="Format YYYY-MM.",
        tracking=True,
    )
    date_from = fields.Date(compute="_compute_period_dates", store=True)
    date_to = fields.Date(compute="_compute_period_dates", store=True)
    ini_valid = fields.Date(string="Table validity start")
    fim_valid = fields.Date(string="Table validity end")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("tables_ok", "Tables ready"),
            ("trial_ok", "Trial balance ready"),
            ("closed", "Closed"),
            ("reopened", "Reopened"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    event_ids = fields.One2many(
        comodel_name="l10n_br_dere.event",
        inverse_name="declaration_id",
    )
    pgcc_account_ids = fields.One2many(
        comodel_name="l10n_br_dere.pgcc.account",
        inverse_name="declaration_id",
    )
    trial_line_ids = fields.One2many(
        comodel_name="l10n_br_dere.trial.line",
        inverse_name="declaration_id",
    )
    batch_ids = fields.One2many(
        comodel_name="l10n_br_dere.batch",
        inverse_name="declaration_id",
    )
    ind_inexist_dedu = fields.Boolean(
        string="Declare no deductions",
        help="Only if the company is subject to D-1121 and has no deductions.",
    )

    _sql_constraints = [
        (
            "company_period_uniq",
            "unique(company_id, per_apur)",
            "There is already a DeRE declaration for this company and period.",
        )
    ]

    @api.depends("company_id", "per_apur")
    def _compute_name(self):
        for rec in self:
            rec.name = f"DeRE {rec.per_apur or ''} / {rec.company_id.name or ''}"

    @api.depends("per_apur")
    def _compute_period_dates(self):
        for rec in self:
            rec.date_from = False
            rec.date_to = False
            if rec.per_apur and re.match(r"^20\d{2}-(0[1-9]|1[0-2])$", rec.per_apur):
                year, month = map(int, rec.per_apur.split("-"))
                last = calendar.monthrange(year, month)[1]
                rec.date_from = date(year, month, 1)
                rec.date_to = date(year, month, last)

    @api.constrains("per_apur")
    def _check_per_apur(self):
        for rec in self:
            if rec.per_apur and not re.match(
                r"^20\d{2}-(0[1-9]|1[0-2])$", rec.per_apur
            ):
                raise ValidationError(_("Assessment period must use the YYYY-MM mask."))

    def _header_vals(self, extra=None, event_type=None):
        self.ensure_one()
        company = self.company_id
        vals = {
            "id": self.env["l10n_br_dere.event"]._generate_event_id(
                event_type=event_type,
                company=company,
                tp_amb=company.dere_tp_amb or "2",
            ),
            "tpOper": "1",
            "tpAmb": company.dere_tp_amb or "2",
            "aplicEmi": "1",
            "verAplic": company.dere_ver_aplic or DEFAULT_VER_APLIC,
            "nrInsc": company._dere_cnpj_root(),
            "iniValid": fields.Date.to_string(self.ini_valid or self.date_from),
            "fimValid": fields.Date.to_string(self.fim_valid)
            if self.fim_valid
            else False,
            "perApur": self.per_apur,
        }
        if extra:
            vals.update(extra)
        if not vals["nrInsc"] or len(vals["nrInsc"]) != 8:
            raise UserError(_("Set a valid 8-digit CNPJ root on the company."))
        return vals

    def _latest_event(self, event_type):
        self.ensure_one()
        events = self.event_ids.filtered(lambda ev: ev.event_type == event_type)
        return events.sorted("id")[-1:]

    def _can_create_next_event(self, event_type):
        self.ensure_one()
        if event_type == EVENT_D1198:
            return self.state == "closed"
        if event_type in (EVENT_D1101, EVENT_D1199):
            latest = self._latest_event(EVENT_D1198)
            return bool(latest and latest.state == "accepted")
        return False

    def _get_or_create_event(self, event_type):
        self.ensure_one()
        events = self.event_ids.filtered(lambda ev: ev.event_type == event_type)
        if events.filtered(
            lambda ev: ev.state in ("sent", "accepted")
        ) and not self._can_create_next_event(event_type):
            if event_type in (EVENT_D1101, EVENT_D1199):
                raise UserError(
                    _("D-1198 must be accepted before generating a new %s.")
                    % event_type
                )
            raise UserError(
                _("Event %s was already sent or accepted and cannot be regenerated.")
                % event_type
            )
        event = events.filtered(lambda ev: ev.state in ("draft", "generated"))[:1]
        if event:
            return event
        company = self.company_id
        return self.env["l10n_br_dere.event"].create(
            {
                "declaration_id": self.id,
                "event_type": event_type,
                "tp_amb": company.dere_tp_amb or "2",
                "ver_aplic": company.dere_ver_aplic or DEFAULT_VER_APLIC,
            }
        )

    def _activity_codes(self, table_code):
        return self.company_id.dere_activity_ids.filtered(
            lambda act: act.table_code == table_code
        ).mapped("code")

    def action_generate_d1001(self):
        for rec in self:
            rec._generate_d1001()
        return True

    def _generate_d1001(self):
        self.ensure_one()
        company = self.company_id
        if not company.dere_reg_trib_princ:
            raise UserError(_("Set the DeRE main tax regime on the company."))
        secund = [company.dere_reg_trib_secund] if company.dere_reg_trib_secund else []
        if company.dere_reg_trib_princ in secund:
            raise UserError(
                _("The secondary tax regime cannot repeat the main regime.")
            )
        vals = self._header_vals(
            {
                "regTribPrinc": company.dere_reg_trib_princ,
                "regTribSecund": secund,
                "indNatTrib": company.dere_ind_nat_trib or "0",
                "tpAtividadeFinanc": self._activity_codes("21"),
                "tpAtividadeSaude": self._activity_codes("31"),
                "tpAtividadeProg": self._activity_codes("41"),
            },
            event_type=EVENT_D1001,
        )
        regimes = {company.dere_reg_trib_princ, *secund}
        if "1" in regimes and not vals["tpAtividadeFinanc"]:
            raise UserError(_("Financial-services activities are required."))
        if "2" in regimes and not vals["tpAtividadeSaude"]:
            raise UserError(_("Health-plan activities are required."))
        if "3" in regimes and not vals["tpAtividadeProg"]:
            raise UserError(_("Prize-contest activities are required."))
        if "1" not in regimes:
            vals["tpAtividadeFinanc"] = []
        if "2" not in regimes:
            vals["tpAtividadeSaude"] = []
        if "3" not in regimes:
            vals["tpAtividadeProg"] = []
        event = self._get_or_create_event(EVENT_D1001)
        vals["id"] = event.event_id_attr or vals["id"]
        event.event_id_attr = vals["id"]
        event._store_xml(xml_builder.build_d1001(vals))
        return event

    def action_generate_d1011(self):
        for rec in self:
            rec._generate_d1011()
        return True

    def _sync_pgcc_from_accounts(self):
        self.ensure_one()
        self.pgcc_account_ids.unlink()
        accounts = self.env["account.account"].search(
            [
                ("company_ids", "in", self.company_id.ids),
                ("l10n_br_dere_cta_ref", "!=", False),
            ]
        )
        if not accounts:
            raise UserError(_("Map at least one account with a DeRE referential code."))
        rows = []
        codes = set()
        for account in accounts:
            c_cta = account.l10n_br_dere_cta
            if not c_cta or c_cta in codes:
                continue
            codes.add(c_cta)
            parent = account.l10n_br_dere_cta_sup_id
            rows.append(
                {
                    "declaration_id": self.id,
                    "account_id": account.id,
                    "dere12_cCta": c_cta,
                    "dere12_cCtaInterna": account.l10n_br_dere_cta_interna
                    or re.sub(r"[^0-9A-Za-z]", "", account.code or ""),
                    "dere12_cDbrMista": account.l10n_br_dere_dbr_mista or "000",
                    "dere12_nomeCta": (account.name or "")[:100],
                    "dere12_indCta": account.l10n_br_dere_ind_cta or "A",
                    "dere12_descCta": account.l10n_br_dere_desc_cta or account.name,
                    "dere12_cCtaSup": parent.l10n_br_dere_cta if parent else False,
                    "dere12_cCtaRef": account.l10n_br_dere_cta_ref,
                    "dere12_nivelCta": account.l10n_br_dere_nivel_cta or 1,
                    "dere12_natCta": account.l10n_br_dere_nat_cta or "V",
                    "dere12_codNat": account.l10n_br_dere_cod_nat or "1",
                    "tax_code_id": account.l10n_br_dere_cod_trib.id,
                    "dere12_indTribISS": account.l10n_br_dere_ind_trib_iss,
                    "dere12_iniVig": self.ini_valid or self.date_from,
                    "dere12_fimVig": self.fim_valid,
                }
            )
        self.env["l10n_br_dere.pgcc.account"].create(rows)
        missing_parents = {
            line.dere12_cCtaSup
            for line in self.pgcc_account_ids
            if line.dere12_cCtaSup and line.dere12_cCtaSup not in codes
        }
        if missing_parents:
            raise UserError(
                _("Parent DeRE accounts are missing from the chart: %s")
                % ", ".join(sorted(missing_parents))
            )
        return self.pgcc_account_ids

    def _generate_d1011(self):
        self.ensure_one()
        company = self.company_id
        if not company.dere_plano_cta_ref or company.dere_plano_cta_ref not in dict(
            PLANO_CTA_REF
        ):
            raise UserError(_("Set the DeRE referential chart on the company."))
        if not company.dere_freq_encerr or company.dere_freq_encerr not in dict(
            FREQ_ENCERR
        ):
            raise UserError(_("Set the DeRE closing frequency on the company."))
        lines = self._sync_pgcc_from_accounts()
        vals = self._header_vals(
            {
                "planoCtaRef": company.dere_plano_cta_ref,
                "freqEncerr": company.dere_freq_encerr,
            },
            event_type=EVENT_D1011,
        )
        event = self._get_or_create_event(EVENT_D1011)
        vals["id"] = event.event_id_attr or vals["id"]
        event.event_id_attr = vals["id"]
        event._store_xml(
            xml_builder.build_d1011(vals, [line._to_xml_vals() for line in lines])
        )
        if self.event_ids.filtered(
            lambda ev: ev.event_type == EVENT_D1001
            and ev.state in ("generated", "accepted")
        ):
            self.state = "tables_ok"
        return event

    def action_generate_tables(self):
        for rec in self:
            rec._generate_d1001()
            rec._generate_d1011()
            rec.state = "tables_ok"
        return True

    def _reset_months(self, freq):
        mapping = {
            "A": {1},
            "S": {1, 7},
            "Q": {1, 5, 9},
            "T": {1, 4, 7, 10},
            "B": {1, 3, 5, 7, 9, 11},
            "M": set(range(1, 13)),
        }
        return mapping.get(freq or "M", {1})

    def _account_balances(self):
        self.ensure_one()
        AccountMoveLine = self.env["account.move.line"]
        domain_base = [
            ("company_id", "=", self.company_id.id),
            ("parent_state", "=", "posted"),
            ("account_id", "in", self.pgcc_account_ids.account_id.ids),
            ("display_type", "not in", ("line_section", "line_note")),
        ]
        opening = defaultdict(lambda: 0.0)
        period = defaultdict(lambda: {"debit": 0.0, "credit": 0.0})
        if self.date_from:
            for line in AccountMoveLine.search(
                domain_base + [("date", "<", self.date_from)]
            ):
                opening[line.account_id.id] += line.balance
        for line in AccountMoveLine.search(
            domain_base
            + [
                ("date", ">=", self.date_from),
                ("date", "<=", self.date_to),
            ]
        ):
            period[line.account_id.id]["debit"] += line.debit
            period[line.account_id.id]["credit"] += line.credit
        return opening, period

    def action_generate_d1101(self):
        for rec in self:
            rec._generate_d1101()
        return True

    def _generate_d1101(self):
        self.ensure_one()
        if not self.pgcc_account_ids:
            self._sync_pgcc_from_accounts()
        opening, period = self._account_balances()
        month = int(self.per_apur.split("-")[1])
        reset_months = self._reset_months(self.company_id.dere_freq_encerr)
        self.trial_line_ids.unlink()
        rows = []
        for pgcc in self.pgcc_account_ids.filtered(
            lambda acc: acc.dere12_indCta == "A"
        ):
            debit = period[pgcc.account_id.id]["debit"]
            credit = period[pgcc.account_id.id]["credit"]
            if pgcc.dere12_codNat in ("4", "5") and month in reset_months:
                open_bal = 0.0
            else:
                open_bal = opening[pgcc.account_id.id]
            close_bal = open_bal + debit - credit
            if not any((open_bal, debit, credit, close_bal)):
                continue
            taxable = bool(pgcc.tax_code_id)
            net = debit - credit
            v_apur = abs(net) if taxable else 0.0
            rows.append(
                {
                    "declaration_id": self.id,
                    "pgcc_account_id": pgcc.id,
                    "dere12_natSaldoInic": "D" if open_bal >= 0 else "C",
                    "dere12_vSaldoInic": abs(open_bal),
                    "dere12_vMovDebt": abs(debit),
                    "dere12_vMovCred": abs(credit),
                    "dere12_natSaldoFinal": "D" if close_bal >= 0 else "C",
                    "dere12_vSaldoFinal": abs(close_bal),
                    "dere12_natVApur": ("D" if net >= 0 else "C") if v_apur else False,
                    "dere12_vApur": v_apur,
                }
            )
        if not rows:
            raise UserError(_("No analytic DeRE movement found for this period."))
        self.env["l10n_br_dere.trial.line"].create(rows)
        vals = self._header_vals(event_type=EVENT_D1101)
        event = self._get_or_create_event(EVENT_D1101)
        vals["id"] = event.event_id_attr or vals["id"]
        event.event_id_attr = vals["id"]
        event._store_xml(
            xml_builder.build_d1101(
                vals, [line._to_xml_vals() for line in self.trial_line_ids]
            )
        )
        self.state = "trial_ok"
        return event

    def action_generate_d1199(self):
        for rec in self:
            rec._generate_d1199()
        return True

    def _generate_d1199(self):
        self.ensure_one()
        if self.state not in ("trial_ok", "reopened", "closed"):
            raise UserError(_("Generate the trial balance before closing."))
        trial = self._latest_event(EVENT_D1101)
        if not trial:
            raise UserError(_("D-1101 must exist before D-1199."))
        d1198 = self._latest_event(EVENT_D1198)
        if d1198 and d1198.state == "accepted" and trial.id < d1198.id:
            raise UserError(
                _("Generate a new trial balance after reopening before closing.")
            )
        extra = {}
        if self.ind_inexist_dedu:
            if not self.company_id.dere_subject_d1121:
                raise UserError(
                    _(
                        "Do not set the no-deductions flag if the company is "
                        "not subject to D-1121."
                    )
                )
            extra["indInexistDedu"] = "1"
        vals = self._header_vals(extra, event_type=EVENT_D1199)
        event = self._get_or_create_event(EVENT_D1199)
        vals["id"] = event.event_id_attr or vals["id"]
        event.event_id_attr = vals["id"]
        event._store_xml(xml_builder.build_d1199(vals))
        self.state = "closed"
        return event

    def action_mark_reopened(self):
        for rec in self:
            rec._generate_d1198()
        return True

    def _d1199_reopen_receipt(self):
        self.ensure_one()
        closing = self._latest_event(EVENT_D1199)
        receipt = (closing.nr_recibo or "").strip() if closing else ""
        expected = (self.per_apur or "").replace("-", "")
        if (
            not closing
            or closing.state != "accepted"
            or not re.fullmatch(D1199_RECEIPT_RE, receipt)
            or receipt[:4] != "1199"
            or receipt[5:11] != expected
        ):
            raise UserError(
                _(
                    "Reopening requires an accepted D-1199 receipt "
                    "1199-%s-... for this period."
                )
                % expected
            )
        return receipt

    def _generate_d1198(self):
        self.ensure_one()
        if self.state != "closed":
            raise UserError(_("Only a closed period can be reopened."))
        vals = self._header_vals(
            {"nrReciboReab": self._d1199_reopen_receipt()},
            event_type=EVENT_D1198,
        )
        event = self._get_or_create_event(EVENT_D1198)
        vals["id"] = event.event_id_attr or vals["id"]
        event.event_id_attr = vals["id"]
        event._store_xml(xml_builder.build_d1198(vals))
        self.state = "reopened"
        return event

    def _assert_send_order(self, event_types):
        self.ensure_one()
        types = set(event_types)
        if len(types) > 1:
            raise UserError(_("Send one DeRE event type per batch."))
        if types & set(TABLE_EVENTS) and types & set(PERIODIC_EVENTS):
            raise UserError(
                _("Do not send table events and periodic events in the same batch.")
            )
        if EVENT_D1011 in types:
            d1001 = self._latest_event(EVENT_D1001)
            if not d1001 or d1001.state != "accepted":
                raise UserError(_("D-1001 must be accepted before sending D-1011."))
        if EVENT_D1198 in types:
            closing = self._latest_event(EVENT_D1199)
            if not closing or closing.state != "accepted" or not closing.nr_recibo:
                raise UserError(_("D-1199 must be accepted before sending D-1198."))
        if EVENT_D1199 in types:
            d1101 = self._latest_event(EVENT_D1101)
            if not d1101:
                raise UserError(_("D-1101 must exist before D-1199."))
            if not d1101.nr_recibo:
                raise UserError(
                    _("D-1101 processing receipt is required before sending D-1199.")
                )

    def _next_events(self, event_types):
        self.ensure_one()
        for event_type in event_types:
            events = self.event_ids.filtered(
                lambda ev, current=event_type: ev.event_type == current
                and ev.xml_content
                and ev.state == "generated"
            )
            if events:
                return events[:1]
        return self.env["l10n_br_dere.event"]

    def action_send_tables(self):
        for rec in self:
            rec._send_events(rec._next_events(TABLE_EVENTS))
        return True

    def action_send_periodics(self):
        for rec in self:
            rec._send_events(rec._next_events(PERIODIC_EVENTS))
        return True

    def _get_dere_certificate(self):
        self.ensure_one()
        company = self.company_id
        if not company.certificate_nfe_id and not company.certificate_ecnpj_id:
            raise UserError(
                _(
                    "Configure an A1 certificate on the company before sending "
                    "DeRE events."
                )
            )
        return company._get_br_ecertificate()

    def _send_events(self, events):
        self.ensure_one()
        if not events:
            raise UserError(_("There is no generated event to send."))
        self._assert_send_order(events.mapped("event_type"))
        certificado = self._get_dere_certificate()
        xml = xml_builder.build_lote(
            self.company_id._dere_cnpj_root(),
            [
                {
                    "id": ev.event_id_attr,
                    "xml": xml_builder.sign_event(
                        ev.xml_content, certificado, ev.event_id_attr
                    ),
                }
                for ev in events
            ],
        )
        batch = self.env["l10n_br_dere.batch"].create(
            {
                "name": f"{self.per_apur} {', '.join(events.mapped('event_type'))}",
                "declaration_id": self.id,
                "tp_amb": self.company_id.dere_tp_amb or "2",
                "event_ids": [(6, 0, events.ids)],
                "xml_content": xml,
            }
        )
        result = self.env["l10n_br_dere.receita.integra"].send_batch(
            self.company_id, xml
        )
        batch.write(
            {
                "state": "sent" if result["ok"] else "error",
                "response_text": result["text"],
                "protocol": self._extract_protocol(result["text"]),
            }
        )
        events.write(
            {
                "state": "sent" if result["ok"] else "rejected",
                "protocol": batch.protocol,
            }
        )
        if not result["ok"]:
            raise UserError(
                _("Receita Integra rejected the batch: %s") % result["text"]
            )
        return batch

    def action_consult_results(self):
        for rec in self:
            batches = rec.batch_ids.filtered(
                lambda batch: batch.protocol and batch.state == "sent"
            )
            if not batches:
                raise UserError(_("There is no sent batch with a protocol to consult."))
            batches.action_consult()
        return True

    def action_apply_return_xml(self, xml_content):
        self.ensure_one()
        parsed = xml_builder.parse_return(xml_content)
        return self._apply_parsed_return(self.event_ids, parsed)

    def _apply_parsed_return(self, events, parsed, protocol=None):
        target = events
        if parsed.get("tpEv"):
            target = events.filtered(lambda ev: ev.event_type == parsed["tpEv"])
        if not target:
            return False
        return self.apply_return(
            target[0],
            parsed.get("cdRetorno") or "0",
            desc_retorno=parsed.get("descRetorno"),
            nr_recibo=parsed.get("nrRecibo"),
            protocol=parsed.get("protocoloLote") or protocol,
            occurrences=parsed.get("ocorrencias"),
        )

    def apply_return(
        self,
        event,
        cd_retorno,
        desc_retorno=None,
        nr_recibo=None,
        protocol=None,
        occurrences=None,
    ):
        event.write(
            {
                "cd_retorno": cd_retorno,
                "desc_retorno": desc_retorno,
                "nr_recibo": nr_recibo,
                "protocol": protocol or event.protocol,
                "state": "accepted" if cd_retorno == "1" else "rejected",
            }
        )
        if occurrences:
            event.occurrence_ids.unlink()
            self.env["l10n_br_dere.event.occurrence"].create(
                [
                    {
                        "event_id": event.id,
                        "codigo": item.get("codigo") or "0",
                        "descricao": item.get("descricao") or "",
                        "tipo": item.get("tipo") or "1",
                        "localizacao": item.get("localizacao"),
                    }
                    for item in occurrences
                ]
            )
        return True

    def _apply_consult_result(self, batch, xml_content):
        self.ensure_one()
        if not xml_content or "<" not in xml_content:
            return False
        try:
            parsed = xml_builder.parse_return(xml_content)
        except etree.XMLSyntaxError:
            return False
        cd_resposta = str(parsed.get("cdResposta") or "")
        if cd_resposta == "1":
            return False
        if parsed.get("cdRetorno"):
            self._apply_parsed_return(
                batch.event_ids, parsed, parsed.get("protocoloLote") or batch.protocol
            )
        if cd_resposta in ("4", "5", "7", "9"):
            batch.state = "error"
            return False
        pending = batch.event_ids.filtered(lambda ev: ev.state == "sent")
        if cd_resposta in ("2", "3") or (batch.event_ids and not pending):
            batch.state = "done"
        return True

    def _extract_protocol(self, text):
        if not text:
            return False
        stripped = text.strip()
        if stripped.startswith("{"):
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                return False
            return payload.get("protocoloLote") or payload.get("protocolo") or False
        if "<" not in stripped:
            return False
        try:
            parsed = xml_builder.parse_return(text)
        except etree.XMLSyntaxError:
            return False
        return parsed.get("protocoloLote") or parsed.get("protocolo") or False
