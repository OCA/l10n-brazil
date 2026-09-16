# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar
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

    def _header_vals(self, extra=None):
        self.ensure_one()
        company = self.company_id
        vals = {
            "id": self.env["l10n_br_dere.event"]._generate_event_id(),
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

    def _get_or_create_event(self, event_type):
        self.ensure_one()
        event = self.event_ids.filtered(
            lambda ev: ev.event_type == event_type and ev.state != "rejected"
        )[:1]
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
            }
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
                    "c_cta": c_cta,
                    "c_cta_interna": account.l10n_br_dere_cta_interna
                    or re.sub(r"[^0-9A-Za-z]", "", account.code or ""),
                    "c_dbr_mista": account.l10n_br_dere_dbr_mista or "000",
                    "nome_cta": (account.name or "")[:100],
                    "ind_cta": account.l10n_br_dere_ind_cta or "A",
                    "desc_cta": account.l10n_br_dere_desc_cta or account.name,
                    "c_cta_sup": parent.l10n_br_dere_cta if parent else False,
                    "c_cta_ref": account.l10n_br_dere_cta_ref,
                    "nivel_cta": account.l10n_br_dere_nivel_cta or 1,
                    "nat_cta": account.l10n_br_dere_nat_cta or "V",
                    "cod_nat": account.l10n_br_dere_cod_nat or "1",
                    "tax_code_id": account.l10n_br_dere_cod_trib.id,
                    "ind_trib_iss": account.l10n_br_dere_ind_trib_iss,
                    "ini_vig": self.ini_valid or self.date_from,
                    "fim_vig": self.fim_valid,
                }
            )
        self.env["l10n_br_dere.pgcc.account"].create(rows)
        missing_parents = {
            line.c_cta_sup
            for line in self.pgcc_account_ids
            if line.c_cta_sup and line.c_cta_sup not in codes
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
            }
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
        for pgcc in self.pgcc_account_ids.filtered(lambda acc: acc.ind_cta == "A"):
            debit = period[pgcc.account_id.id]["debit"]
            credit = period[pgcc.account_id.id]["credit"]
            if pgcc.cod_nat in ("4", "5") and month in reset_months:
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
                    "nat_saldo_inic": "D" if open_bal >= 0 else "C",
                    "v_saldo_inic": abs(open_bal),
                    "v_mov_debt": abs(debit),
                    "v_mov_cred": abs(credit),
                    "nat_saldo_final": "D" if close_bal >= 0 else "C",
                    "v_saldo_final": abs(close_bal),
                    "nat_v_apur": ("D" if net >= 0 else "C") if v_apur else False,
                    "v_apur": v_apur,
                }
            )
        if not rows:
            raise UserError(_("No analytic DeRE movement found for this period."))
        self.env["l10n_br_dere.trial.line"].create(rows)
        vals = self._header_vals()
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
        trial = self.event_ids.filtered(lambda ev: ev.event_type == EVENT_D1101)
        if not trial:
            raise UserError(_("D-1101 must exist before D-1199."))
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
        vals = self._header_vals(extra)
        event = self._get_or_create_event(EVENT_D1199)
        vals["id"] = event.event_id_attr or vals["id"]
        event.event_id_attr = vals["id"]
        event._store_xml(xml_builder.build_d1199(vals))
        self.state = "closed"
        return event

    def action_mark_reopened(self):
        for rec in self:
            if rec.state != "closed":
                raise UserError(_("Only a closed period can be reopened."))
            rec._get_or_create_event(EVENT_D1198)
            rec.state = "reopened"
        return True

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
            d1001 = self.event_ids.filtered(lambda ev: ev.event_type == EVENT_D1001)
            if not d1001 or d1001[0].state != "accepted":
                raise UserError(_("D-1001 must be accepted before sending D-1011."))
        if EVENT_D1199 in types:
            d1101 = self.event_ids.filtered(lambda ev: ev.event_type == EVENT_D1101)
            if not d1101:
                raise UserError(_("D-1101 must exist before D-1199."))
            if not d1101[0].nr_recibo:
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

    def _send_events(self, events):
        self.ensure_one()
        if not events:
            raise UserError(_("There is no generated event to send."))
        self._assert_send_order(events.mapped("event_type"))
        xml = xml_builder.build_lote(
            self.company_id._dere_cnpj_root(),
            [{"id": ev.event_id_attr, "xml": ev.xml_content} for ev in events],
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
        if result["ok"] and result.get("text") and "<" in result["text"]:
            try:
                parsed = xml_builder.parse_return(result["text"])
            except etree.XMLSyntaxError:
                parsed = {}
            if parsed:
                self._apply_parsed_return(events, parsed, batch.protocol)
        if not result["ok"]:
            raise UserError(
                _("Receita Integra rejected the batch: %s") % result["text"]
            )
        return batch

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

    def _extract_protocol(self, text):
        if not text:
            return False
        match = re.search(r"[0-9A-Za-z-]{10,28}", text)
        return match.group(0) if match else False
