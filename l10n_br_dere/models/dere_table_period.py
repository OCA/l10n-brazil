# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
import re

import requests
from lxml import etree
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_dere_spec.models import xsd_validator
from odoo.addons.l10n_br_dere_spec.models.v1_2.types import (
    FREQ_ENCERR,
    PLANO_CTA_REF,
)

from ..constants import (
    DEFAULT_VER_APLIC,
    EVENT_D1001,
    EVENT_D1011,
    PROTOCOL_RE,
    TABLE_EVENTS,
)
from . import xml_builder

_logger = logging.getLogger(__name__)


class DereTablePeriod(models.Model):
    _name = "l10n_br_dere.table.period"
    _description = "DeRE table validity period"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "l10n_br_dere.event.parent.mixin",
    ]
    _order = "ini_valid desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    ini_valid = fields.Date(string="Validity start", required=True, tracking=True)
    fim_valid = fields.Date(string="Validity end", tracking=True)
    fim_valid_efetiva = fields.Date(
        string="Effective validity end",
        compute="_compute_fim_valid_efetiva",
        store=True,
        tracking=True,
        help="End date applied by the RFB (D-9001) when a later validity of "
        "the same table cut this period.",
    )
    rfb_validity_ids = fields.One2many(
        comodel_name="l10n_br_dere.table.validity",
        inverse_name="table_period_id",
        string="RFB validity of this period",
    )
    rfb_extract_validity_ids = fields.Many2many(
        comodel_name="l10n_br_dere.table.validity",
        compute="_compute_rfb_extract",
        string="RFB validity extract",
    )
    rfb_gap_ids = fields.Many2many(
        comodel_name="l10n_br_dere.table.gap",
        compute="_compute_rfb_extract",
        string="RFB gaps",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("generated", "Generated"),
            ("accepted", "Accepted"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    event_ids = fields.One2many(
        comodel_name="l10n_br_dere.event",
        inverse_name="table_period_id",
    )
    pgcc_account_ids = fields.One2many(
        comodel_name="l10n_br_dere.pgcc.account",
        inverse_name="table_period_id",
    )
    batch_ids = fields.One2many(
        comodel_name="l10n_br_dere.batch",
        inverse_name="table_period_id",
    )
    declaration_ids = fields.One2many(
        comodel_name="l10n_br_dere.declaration",
        inverse_name="table_period_id",
    )
    can_generate_tables = fields.Boolean(compute="_compute_actions")
    can_send_tables = fields.Boolean(compute="_compute_actions")
    can_consult_results = fields.Boolean(compute="_compute_actions")
    can_replace_tables = fields.Boolean(compute="_compute_actions")
    can_exclude_tables = fields.Boolean(compute="_compute_actions")

    _sql_constraints = [
        (
            "company_ini_valid_uniq",
            "unique(company_id, ini_valid)",
            "There is already a DeRE table period for this company and start date.",
        )
    ]

    @api.depends("company_id", "ini_valid", "fim_valid")
    def _compute_name(self):
        for rec in self:
            end = rec.fim_valid or _("open")
            rec.name = (
                f"DeRE tables {rec.ini_valid or ''} / {end} / "
                f"{rec.company_id.name or ''}"
            )

    @api.constrains("ini_valid", "fim_valid")
    def _check_validity(self):
        for rec in self:
            if rec.fim_valid and rec.ini_valid and rec.fim_valid < rec.ini_valid:
                raise ValidationError(
                    _("Table validity end must be on or after the start date.")
                )

    @api.depends(
        "rfb_validity_ids.dere12_fimValidEfetiva",
        "rfb_validity_ids.dere12_indAjusteAuto",
    )
    def _compute_fim_valid_efetiva(self):
        for rec in self:
            cuts = [
                line.dere12_fimValidEfetiva
                for line in rec.rfb_validity_ids
                if line.dere12_indAjusteAuto == "1" and line.dere12_fimValidEfetiva
            ]
            rec.fim_valid_efetiva = min(cuts) if cuts else False

    def _compute_rfb_extract(self):
        validity_model = self.env["l10n_br_dere.table.validity"]
        gap_model = self.env["l10n_br_dere.table.gap"]
        for rec in self:
            domain = [("company_id", "=", rec.company_id.id)]
            rec.rfb_extract_validity_ids = validity_model.search(domain)
            rec.rfb_gap_ids = gap_model.search(domain)

    def _latest_event(self, event_type):
        self.ensure_one()
        events = self._event_records(event_type)
        return events.sorted("id")[-1:]

    def _event_can_be_generated(self, event_type):
        return self._can_include_event(event_type)

    @api.depends(
        "event_ids.state",
        "event_ids.event_type",
        "event_ids.tp_oper",
        "batch_ids.state",
    )
    def _compute_actions(self):
        for rec in self:
            rec.can_generate_tables = all(
                rec._can_include_event(event_type) for event_type in TABLE_EVENTS
            )
            rec.can_replace_tables = all(
                rec._can_replace_or_exclude(event_type) for event_type in TABLE_EVENTS
            )
            rec.can_exclude_tables = rec.can_replace_tables
            rec.can_send_tables = bool(rec._next_events(TABLE_EVENTS))
            rec.can_consult_results = bool(
                rec.batch_ids.filtered(
                    lambda batch: batch.protocol and batch.state == "sent"
                )
            )

    def tables_accepted(self):
        self.ensure_one()
        return bool(self._active_event(EVENT_D1001) and self._active_event(EVENT_D1011))

    @api.model
    def _find_covering(self, company, day):
        if not company or not day:
            return self.browse()
        periods = self.search(
            [
                ("company_id", "=", company.id),
                ("ini_valid", "<=", day),
                "|",
                ("fim_valid_efetiva", ">=", day),
                "&",
                ("fim_valid_efetiva", "=", False),
                "|",
                ("fim_valid", "=", False),
                ("fim_valid", ">=", day),
            ],
            order="ini_valid desc, id desc",
            limit=1,
        )
        return periods

    @api.model
    def _get_or_create_for(self, company, day):
        existing = self._find_covering(company, day)
        if existing:
            return existing
        return self.create({"company_id": company.id, "ini_valid": day.replace(day=1)})

    def _header_vals(self, extra=None, event_type=None, tp_oper="1"):
        self.ensure_one()
        company = self.company_id
        extra = extra or {}
        extra = self._prepare_oper_extra(
            event_type, extra.get("tpOper") or tp_oper or "1", extra
        )
        tp_oper = extra.get("tpOper") or tp_oper or "1"
        vals = {
            "id": self.env["l10n_br_dere.event"]._generate_event_id(
                event_type=event_type,
                company=company,
                tp_amb=company.dere_tp_amb or "2",
            ),
            "tpOper": tp_oper,
            "tpAmb": company.dere_tp_amb or "2",
            "aplicEmi": "1",
            "verAplic": company.dere_ver_aplic or DEFAULT_VER_APLIC,
            "nrInsc": company._dere_cnpj_root(),
            "iniValid": fields.Date.to_string(self.ini_valid),
            "fimValid": fields.Date.to_string(self.fim_valid)
            if self.fim_valid
            else False,
        }
        vals.update(extra)
        if not vals["nrInsc"] or len(vals["nrInsc"]) != 8:
            raise UserError(_("Set a valid 8-digit CNPJ root on the company."))
        return vals

    def _get_or_create_event(self, event_type, tp_oper="1"):
        return self._create_oper_event(
            event_type, tp_oper=tp_oper, parent_field="table_period_id"
        )

    def _activity_codes(self, table_code):
        return self.company_id.dere_activity_ids.filtered(
            lambda act: act.table_code == table_code
        ).mapped("code")

    def action_generate_d1001(self):
        for rec in self:
            rec._generate_d1001()
        return True

    def _generate_d1001(self, tp_oper="1", extra=None):
        self.ensure_one()
        extra = self._prepare_oper_extra(EVENT_D1001, tp_oper, extra)
        company = self.company_id
        if not company.dere_reg_trib_princ:
            raise UserError(_("Set the DeRE main tax regime on the company."))
        secund = [company.dere_reg_trib_secund] if company.dere_reg_trib_secund else []
        if company.dere_reg_trib_princ in secund:
            raise UserError(
                _("The secondary tax regime cannot repeat the main regime.")
            )
        payload = {
            "regTribPrinc": company.dere_reg_trib_princ,
            "regTribSecund": secund,
            "indNatTrib": company.dere_ind_nat_trib or "0",
            "tpAtividadeFinanc": self._activity_codes("21"),
            "tpAtividadeSaude": self._activity_codes("31"),
            "tpAtividadeProg": self._activity_codes("41"),
        }
        payload.update(extra)
        vals = self._header_vals(
            payload,
            event_type=EVENT_D1001,
            tp_oper=tp_oper,
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
        event = self._get_or_create_event(EVENT_D1001, tp_oper=tp_oper)
        vals["id"] = event.event_id_attr or vals["id"]
        event.write(
            {
                "event_id_attr": vals["id"],
                "tp_oper": tp_oper,
                "mot_excl": extra.get("motExcl"),
            }
        )
        event._store_xml(xml_builder.build_d1001(vals))
        return event

    def _account_name_for_xml(self, record):
        self.ensure_one()
        lang = self.company_id.partner_id.lang or "en_US"
        name = record.with_context(lang=lang).name or record.name or ""
        return name[:100]

    def _mapped_pgcc_accounts(self):
        self.ensure_one()
        accounts = self.env["account.account"].search(
            [("company_ids", "in", self.company_id.ids)]
        )
        return accounts.filtered(
            lambda acc: acc._dere_cta_ref() and acc.l10n_br_dere_cta
        )

    def _mapped_pgcc_groups(self, accounts):
        self.ensure_one()
        groups = self.env["account.group"].search(
            [
                ("company_id", "=", self.company_id.root_id.id),
                ("l10n_br_dere_cta_ref", "!=", False),
            ]
        )
        for account in accounts:
            parent = account._dere_parent_group()
            if parent:
                groups |= parent._dere_ancestors()
        return groups

    def _pgcc_row_from_group(self, group, codes):
        c_cta = group.l10n_br_dere_cta
        cta_ref = group._dere_cta_ref()
        if not c_cta or c_cta in codes or not cta_ref:
            return False
        codes.add(c_cta)
        name = self._account_name_for_xml(group)
        return {
            "table_period_id": self.id,
            "group_id": group.id,
            "dere12_cCta": c_cta,
            "dere12_cCtaInterna": group._dere_internal_code(),
            "dere12_cDbrMista": group.l10n_br_dere_dbr_mista or "000",
            "dere12_nomeCta": name,
            "dere12_indCta": "S",
            "dere12_descCta": group.l10n_br_dere_desc_cta or name,
            "dere12_cCtaSup": group.l10n_br_dere_cta_sup,
            "dere12_cCtaRef": cta_ref,
            "dere12_nivelCta": group.l10n_br_dere_nivel_cta or 1,
            "dere12_natCta": group._dere_nat_cta() or "V",
            "dere12_codNat": group._dere_cod_nat() or "1",
            "dere12_iniVig": self.ini_valid,
            "dere12_fimVig": self.fim_valid,
        }

    def _pgcc_row_from_account(self, account, codes):
        c_cta = account.l10n_br_dere_cta
        if not c_cta or c_cta in codes:
            return False
        codes.add(c_cta)
        parent = account._dere_parent_group()
        name = self._account_name_for_xml(account)
        return {
            "table_period_id": self.id,
            "account_id": account.id,
            "dere12_cCta": c_cta,
            "dere12_cCtaInterna": account._dere_internal_code(),
            "dere12_cDbrMista": account.l10n_br_dere_dbr_mista or "000",
            "dere12_nomeCta": name,
            "dere12_indCta": "A",
            "dere12_descCta": account.l10n_br_dere_desc_cta or name,
            "dere12_cCtaSup": parent.l10n_br_dere_cta if parent else False,
            "dere12_cCtaRef": account._dere_cta_ref(),
            "dere12_nivelCta": account.l10n_br_dere_nivel_cta or 1,
            "dere12_natCta": account._dere_nat_cta() or "V",
            "dere12_codNat": account._dere_cod_nat() or "1",
            "tax_code_id": account.l10n_br_dere_cod_trib.id,
            "dere12_indTribISS": account.l10n_br_dere_ind_trib_iss,
            "dere12_iniVig": self.ini_valid,
            "dere12_fimVig": self.fim_valid,
        }

    def _take_existing_pgcc(self, row, by_account, by_group, by_cta, used):
        """Reuse the snapshot line of the same account, group or cCta."""
        candidates = (
            by_account.get(row.get("account_id")),
            by_group.get(row.get("group_id")),
            by_cta.get(row.get("dere12_cCta")),
        )
        for line in candidates:
            if line and line.id not in used:
                used.add(line.id)
                return line
        return self.env["l10n_br_dere.pgcc.account"]

    def _sync_pgcc_from_accounts(self):
        """Refresh the PGCC snapshot without dropping referenced lines.

        Trial-balance and reserve lines keep a restrict FK on the snapshot.
        Rebuilding D-1011 after D-1101 / D-1106 therefore updates the
        existing rows (for example a new ``codTrib``) instead of unlinking
        them.
        """
        self.ensure_one()
        accounts = self._mapped_pgcc_accounts()
        if not accounts:
            raise UserError(_("Map at least one account with a DeRE referential code."))
        missing_tax = accounts.filtered(lambda acc: not acc.l10n_br_dere_cod_trib)
        if missing_tax:
            raise UserError(
                _("Analytic DeRE accounts must have a taxation code: %s")
                % ", ".join(missing_tax.mapped("code"))
            )
        groups = self._mapped_pgcc_groups(accounts)
        rows = []
        codes = set()
        for group in groups.sorted(lambda rec: rec.l10n_br_dere_nivel_cta or 1):
            row = self._pgcc_row_from_group(group, codes)
            if row:
                rows.append(row)
        for account in accounts:
            row = self._pgcc_row_from_account(account, codes)
            if row:
                rows.append(row)
        existing = self.pgcc_account_ids
        by_account = {line.account_id.id: line for line in existing if line.account_id}
        by_group = {line.group_id.id: line for line in existing if line.group_id}
        by_cta = {line.dere12_cCta: line for line in existing}
        used = set()
        create_rows = []
        kept = self.env["l10n_br_dere.pgcc.account"]
        for row in rows:
            match = self._take_existing_pgcc(row, by_account, by_group, by_cta, used)
            if match:
                match.with_context(dere_force_declaration_write=True).write(row)
                kept |= match
            else:
                create_rows.append(row)
        if create_rows:
            self.env["l10n_br_dere.pgcc.account"].create(create_rows)
        leftover = existing - kept
        if leftover:
            trial = self.env["l10n_br_dere.trial.line"].search(
                [("pgcc_account_id", "in", leftover.ids)], limit=1
            )
            reserve = self.env["l10n_br_dere.reserve.line"].search(
                [("pgcc_account_id", "in", leftover.ids)], limit=1
            )
            if trial or reserve:
                raise UserError(
                    _(
                        "The PGCC snapshot cannot drop accounts still used by "
                        "D-1101 or D-1106: %s"
                    )
                    % ", ".join(leftover.mapped("dere12_cCta"))
                )
            leftover.with_context(dere_force_declaration_write=True).unlink()
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

    def action_generate_d1011(self):
        for rec in self:
            rec._generate_d1011()
        return True

    def _generate_d1011(self, tp_oper="1", extra=None):
        self.ensure_one()
        extra = self._prepare_oper_extra(EVENT_D1011, tp_oper, extra)
        company = self.company_id
        if not company.dere_plano_cta_ref or company.dere_plano_cta_ref not in dict(
            PLANO_CTA_REF
        ):
            raise UserError(_("Set the DeRE referential chart on the company."))
        if not company.dere_freq_encerr or company.dere_freq_encerr not in dict(
            FREQ_ENCERR
        ):
            raise UserError(_("Set the DeRE closing frequency on the company."))
        lines = (
            self.pgcc_account_ids if tp_oper == "3" else self._sync_pgcc_from_accounts()
        )
        payload = {
            "planoCtaRef": company.dere_plano_cta_ref,
            "freqEncerr": company.dere_freq_encerr,
        }
        payload.update(extra)
        vals = self._header_vals(
            payload,
            event_type=EVENT_D1011,
            tp_oper=tp_oper,
        )
        event = self._get_or_create_event(EVENT_D1011, tp_oper=tp_oper)
        vals["id"] = event.event_id_attr or vals["id"]
        event.write(
            {
                "event_id_attr": vals["id"],
                "tp_oper": tp_oper,
                "mot_excl": extra.get("motExcl"),
            }
        )
        event._store_xml(
            xml_builder.build_d1011(
                vals,
                [line._to_xml_vals() for line in lines] if tp_oper != "3" else [],
            )
        )
        if self._latest_event(EVENT_D1001).xml_content:
            self.state = "generated"
        return event

    def action_generate_tables(self):
        for rec in self:
            rec._generate_d1001()
            rec._generate_d1011()
            if rec.state == "draft":
                rec.state = "generated"
        return True

    def action_replace_tables(self):
        return self._action_table_operation("2")

    def action_exclude_tables(self):
        return self._action_table_operation("3")

    def _action_table_operation(self, tp_oper):
        self.ensure_one()
        wizard = self.env["l10n_br_dere.event.operation.wizard"].create(
            {
                "table_period_id": self.id,
                "event_type": EVENT_D1011,
                "tp_oper": tp_oper,
                "nova_ini_valid": self.ini_valid,
                "nova_fim_valid": self.fim_valid,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("DeRE table operation"),
            "res_model": "l10n_br_dere.event.operation.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _generate_table_operation(self, tp_oper="2", extra=None):
        self.ensure_one()
        self._generate_d1001(tp_oper=tp_oper, extra=extra)
        self._generate_d1011(tp_oper=tp_oper, extra=extra)
        if self.state == "draft":
            self.state = "generated"
        return True

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

    def _assert_send_order(self, event_types):
        types = set(event_types)
        if len(types) > 1:
            raise UserError(_("Send one DeRE event type per batch."))
        if EVENT_D1011 in types:
            d1001 = self._latest_event(EVENT_D1001)
            if not d1001 or d1001.state != "accepted":
                raise UserError(_("D-1001 must be accepted before sending D-1011."))

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

    def action_send_tables(self):
        result = True
        for rec in self:
            action = rec._send_events(rec._next_events(TABLE_EVENTS))
            if isinstance(action, dict):
                result = action
        return result

    def _send_events(self, events):
        self.ensure_one()
        if not events:
            raise UserError(_("There is no generated event to send."))
        self._assert_send_order(events.mapped("event_type"))
        certificado = self._get_dere_certificate()
        signed_events = []
        for ev in events:
            signed_xml = xml_builder.sign_event(
                ev.xml_content, certificado, ev.event_id_attr
            )
            ev._assert_valid_xml(signed_xml, signed=True)
            signed_events.append({"id": ev.event_id_attr, "xml": signed_xml})
        xml = xml_builder.build_lote(self.company_id._dere_cnpj_root(), signed_events)
        lote_errors = xsd_validator.validate_lote(xml)
        if lote_errors:
            raise UserError(
                _("DeRE batch XML failed official XSD validation:\n%s")
                % "\n".join(lote_errors[:8])
            )
        batch = self.env["l10n_br_dere.batch"].create(
            {
                "name": f"{self.ini_valid} {', '.join(events.mapped('event_type'))}",
                "table_period_id": self.id,
                "tp_amb": self.company_id.dere_tp_amb or "2",
                "event_ids": [(6, 0, events.ids)],
                "xml_content": xml,
            }
        )
        try:
            result = self.env["l10n_br_dere.receita.integra"].send_batch(
                self.company_id, xml
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            batch.write({"state": "unknown", "response_text": str(exc)})
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Transmission unknown"),
                    "message": _(
                        "The DeRE batch request failed before a protocol was "
                        "received. Check the transmission before sending again."
                    ),
                    "type": "warning",
                    "sticky": True,
                    "next": {"type": "ir.actions.client", "tag": "soft_reload"},
                },
            }
        batch.write(
            {
                "state": "sent" if result["ok"] else "error",
                "response_text": result["text"],
                "protocol": self._extract_protocol(result["text"]),
            }
        )
        if result["ok"]:
            batch._schedule_next_consult()
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
        consulted = self.env["l10n_br_dere.batch"]
        for rec in self:
            transmitted = rec.batch_ids.filtered(lambda batch: batch.protocol)
            if not transmitted:
                raise UserError(_("There is no sent batch with a protocol to consult."))
            batches = transmitted.filtered(lambda batch: batch.state == "sent")
            batches.action_consult()
            consulted |= batches
        if not consulted:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Nothing to consult"),
                    "message": _("Every transmitted batch was already processed."),
                    "type": "info",
                    "next": {"type": "ir.actions.client", "tag": "soft_reload"},
                },
            }
        return True

    def apply_return(
        self,
        event,
        cd_retorno,
        desc_retorno=None,
        nr_recibo=None,
        protocol=None,
        occurrences=None,
        payload=None,
    ):
        event.write(
            {
                "cd_retorno": cd_retorno,
                "desc_retorno": desc_retorno,
                "nr_recibo": nr_recibo,
                "protocol": protocol or event.protocol,
                "state": "accepted" if cd_retorno == "1" else "rejected",
                **event._return_payload_vals(payload),
            }
        )
        event._check_return_schema()
        if event.tp_oper == "2" and event.state == "accepted":
            self._apply_nova_validade(event)
        if self.tables_accepted():
            self.state = "accepted"
        elif self.state == "accepted":
            self.state = "generated"
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
        event._return_parent()._apply_return_content(event, payload)
        return True

    def _apply_return_content(self, event, payload):
        res = super()._apply_return_content(event, payload)
        extract = (payload or {}).get("extract")
        if extract:
            self._store_rfb_extract(event, extract)
        return res

    def _periods_by_receipt(self, event_type, receipts):
        self.ensure_one()
        events = self.env["l10n_br_dere.event"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("event_type", "=", event_type),
                ("table_period_id", "!=", False),
                ("nr_recibo", "in", [receipt for receipt in receipts if receipt]),
            ]
        )
        return {event.nr_recibo: event.table_period_id.id for event in events}

    def _store_rfb_extract(self, event, extract):
        """Replace the company photo of ``event``'s table with the D-9001 one.

        The extract lists every validity in force at the RFB for that table,
        so older photos of the same table are dropped.
        """
        self.ensure_one()
        common = {
            "company_id": self.company_id.id,
            "event_type": event.event_type,
            "event_id": event.id,
        }
        domain = [
            ("company_id", "=", self.company_id.id),
            ("event_type", "=", event.event_type),
        ]
        validity_model = self.env["l10n_br_dere.table.validity"].sudo()
        gap_model = self.env["l10n_br_dere.table.gap"].sudo()
        validity_model.search(domain).unlink()
        gap_model.search(domain).unlink()
        lines = extract.get("validity") or []
        periods = self._periods_by_receipt(
            event.event_type, [line.get("nrRecibo") for line in lines]
        )
        validity = validity_model.create(
            [
                {
                    **common,
                    **{f"dere12_{key}": value for key, value in line.items()},
                    "table_period_id": periods.get(line.get("nrRecibo"), False),
                }
                for line in lines
            ]
        )
        gaps = gap_model.create(
            [
                {**common, **{f"dere12_{key}": value for key, value in gap.items()}}
                for gap in extract.get("gaps") or []
            ]
        )
        self.invalidate_model(["rfb_extract_validity_ids", "rfb_gap_ids"])
        issues = self._rfb_extract_issues(validity, gaps)
        if issues:
            self.message_post(
                body=Markup("%s<br/>%s")
                % (
                    _("The RFB validity extract needs attention:"),
                    Markup("<br/>").join(issues),
                )
            )
        return validity

    def _rfb_extract_issues(self, validity, gaps):
        issues = []
        for line in validity:
            if not line.table_period_id:
                issues.append(
                    _(
                        "%(event)s receipt %(receipt)s is in force at the RFB "
                        "but belongs to no local table period."
                    )
                    % {"event": line.event_type, "receipt": line.dere12_nrRecibo}
                )
            elif line.dere12_indAjusteAuto == "1":
                issues.append(
                    _("%(event)s validity %(period)s was cut by the RFB on %(end)s.")
                    % {
                        "event": line.event_type,
                        "period": line.table_period_id.display_name,
                        "end": line.dere12_fimValidEfetiva or "-",
                    }
                )
        for gap in gaps:
            issues.append(
                _("%(event)s has no validity at the RFB from %(start)s to %(end)s.")
                % {
                    "event": gap.event_type,
                    "start": gap.dere12_iniLacuna,
                    "end": gap.dere12_fimLacuna or _("an open end"),
                }
            )
        return issues

    def _apply_nova_validade(self, event):
        if not event.xml_content:
            return
        root = etree.fromstring(event.xml_content.encode("utf-8"))
        nova = root.find(".//{*}novaValidade")
        if nova is None:
            return
        ini = nova.findtext("{*}iniValid")
        fim = nova.findtext("{*}fimValid")
        vals = {}
        if ini:
            vals["ini_valid"] = ini
        vals["fim_valid"] = fim or False
        if vals:
            self.write(vals)

    def _reject_batch_events(self, batch, parsed):
        events = batch.event_ids.filtered(lambda ev: ev.state == "sent")
        events.with_context(dere_force_event_write=True).write(
            {
                "state": "rejected",
                "cd_retorno": "0",
                "desc_retorno": parsed.get("descResposta") or parsed.get("descRetorno"),
            }
        )
        occurrences = parsed.get("ocorrencias") or []
        if occurrences:
            events.occurrence_ids.unlink()
            self.env["l10n_br_dere.event.occurrence"].create(
                [
                    {
                        "event_id": event.id,
                        "codigo": item.get("codigo") or "0",
                        "descricao": item.get("descricao") or "",
                        "tipo": item.get("tipo") or "1",
                        "localizacao": item.get("localizacao"),
                    }
                    for event in events
                    for item in occurrences
                ]
            )

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
        if cd_resposta in ("4", "5", "7", "9"):
            batch.state = "error"
            self._reject_batch_events(batch, parsed)
            return False
        protocol = (
            parsed.get("protocoloLote") or parsed.get("protocolo") or batch.protocol
        )
        applied = False
        for item in parsed.get("events") or []:
            target = batch.event_ids
            if item.get("id"):
                event_id = item["id"]
                matched = target.filtered(
                    lambda ev, current=event_id: ev.event_id_attr == current
                )
                if matched:
                    target = matched
            if item.get("tpEv"):
                event_type = item["tpEv"]
                target = target.filtered(
                    lambda ev, current=event_type: ev.event_type == current
                )
            if not target:
                continue
            self.apply_return(
                target[0],
                item.get("cdRetorno") or "0",
                desc_retorno=item.get("descRetorno"),
                nr_recibo=item.get("nrRecibo"),
                protocol=item.get("protocoloLote") or protocol,
                occurrences=item.get("ocorrencias"),
                payload=item,
            )
            applied = True
        pending = batch.event_ids.filtered(lambda ev: ev.state == "sent")
        if cd_resposta in ("2", "3") or (batch.event_ids and not pending):
            batch.state = "done"
            return True
        return applied

    def _extract_protocol(self, text):
        if not text:
            return False
        stripped = text.strip()
        if re.fullmatch(PROTOCOL_RE, stripped):
            return stripped
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
