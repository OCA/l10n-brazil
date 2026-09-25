# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_dere_spec.models import xsd_validator
from odoo.addons.l10n_br_dere_spec.models.v1_2.types import (
    APLIC_EMI,
    CD_RETORNO,
    MOT_EXCL,
    TP_AMB,
    TP_OPER_DEDUCAO,
)

from ..constants import (
    BRASILIA_TZ,
    EVENT_D1001,
    EVENT_D1011,
    EVENT_D1101,
    EVENT_D1106,
    EVENT_D1121,
    EVENT_D1198,
    EVENT_D1199,
    EVENT_ID_INSCRIPTION_TYPE,
    EVENT_TYPES,
    RETURN_TYPE_BY_TAG,
    RETURN_TYPES,
    STRUCTURED_EVENT_ID,
)
from . import xml_builder

OPERABLE_EVENT_TYPES = frozenset(
    {EVENT_D1001, EVENT_D1011, EVENT_D1101, EVENT_D1106, EVENT_D1121}
)


class DereEvent(models.Model):
    _name = "l10n_br_dere.event"
    _description = "DeRE event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(compute="_compute_name", store=True)
    declaration_id = fields.Many2one(
        comodel_name="l10n_br_dere.declaration",
        ondelete="cascade",
        index=True,
    )
    table_period_id = fields.Many2one(
        comodel_name="l10n_br_dere.table.period",
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_company_id",
        store=True,
        index=True,
    )
    event_type = fields.Selection(EVENT_TYPES, required=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("generated", "Generated"),
            ("sent", "Sent"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    tp_oper = fields.Selection(
        TP_OPER_DEDUCAO, string="Operation type", default="1", required=True
    )
    mot_excl = fields.Selection(MOT_EXCL, string="Exclusion reason")
    nr_proc = fields.Char(string="Process number", size=21)
    nr_recibo_prev = fields.Char(string="Previous receipt", size=31)
    tp_amb = fields.Selection(TP_AMB, string="Environment", required=True)
    aplic_emi = fields.Selection(APLIC_EMI, string="Issuer", default="1", required=True)
    ver_aplic = fields.Char(string="Application version", size=20, required=True)
    event_id_attr = fields.Char(string="Official event id", size=42, copy=False)
    xml_content = fields.Text(string="XML")
    xml_hash = fields.Char(string="XML hash", size=64)
    protocol = fields.Char(string="Batch protocol", size=28, tracking=True)
    nr_recibo = fields.Char(string="Processing receipt", size=31, tracking=True)
    cd_retorno = fields.Selection(CD_RETORNO, string="Return code")
    desc_retorno = fields.Char(string="Return description")
    occurrence_ids = fields.One2many(
        comodel_name="l10n_br_dere.event.occurrence",
        inverse_name="event_id",
    )
    return_type = fields.Selection(RETURN_TYPES, string="Return event", copy=False)
    return_xml = fields.Text(string="Return XML", copy=False)
    seq_evento = fields.Char(string="Event version sequence", size=2, copy=False)
    dh_recepcao = fields.Datetime(string="Received at", copy=False)
    dh_process = fields.Datetime(string="Processed at", copy=False)
    nr_recibo_pgcc = fields.Char(string="PGCC receipt used", size=31, copy=False)
    total_ids = fields.One2many(
        comodel_name="l10n_br_dere.event.total",
        inverse_name="event_id",
        string="RFB totals",
    )
    can_replace_event = fields.Boolean(
        string="Can replace event", compute="_compute_event_operations"
    )
    can_exclude_event = fields.Boolean(
        string="Can exclude event", compute="_compute_event_operations"
    )
    can_rectify_event = fields.Boolean(
        string="Can rectify event", compute="_compute_event_operations"
    )

    _SENT_WRITE_FIELDS = frozenset(
        {
            "state",
            "protocol",
            "nr_recibo",
            "cd_retorno",
            "desc_retorno",
            "return_type",
            "return_xml",
            "seq_evento",
            "dh_recepcao",
            "dh_process",
            "nr_recibo_pgcc",
        }
    )

    def write(self, vals):
        if not self.env.context.get("dere_force_event_write"):
            locked = self.filtered(lambda ev: ev.state in ("accepted", "rejected"))
            if locked:
                raise UserError(_("Processed DeRE events cannot be modified."))
            sent = self.filtered(lambda ev: ev.state == "sent")
            if sent and set(vals) - self._SENT_WRITE_FIELDS:
                raise UserError(
                    _("Sent DeRE events can only be updated with the consult result.")
                )
        return super().write(vals)

    def unlink(self):
        locked = self.filtered(
            lambda ev: ev.state not in ("draft", "generated")
            and not (
                ev.env.context.get("dere_force_unlink")
                or (ev.company_id and ev.company_id._dere_can_force_delete())
            )
        )
        if locked:
            raise UserError(_("Only draft or generated events can be deleted."))
        return super().unlink()

    @api.depends("declaration_id.company_id", "table_period_id.company_id")
    def _compute_company_id(self):
        for rec in self:
            rec.company_id = (
                rec.declaration_id.company_id or rec.table_period_id.company_id
            )

    @api.depends(
        "event_type",
        "state",
        "tp_oper",
        "declaration_id.can_replace_trial",
        "declaration_id.can_replace_d1106",
        "declaration_id.can_replace_d1121",
        "declaration_id.can_rectify_d1121",
        "declaration_id.event_ids.state",
        "declaration_id.event_ids.tp_oper",
        "table_period_id.event_ids.state",
        "table_period_id.event_ids.tp_oper",
    )
    def _compute_event_operations(self):
        for rec in self:
            rec.can_replace_event = False
            rec.can_exclude_event = False
            rec.can_rectify_event = False
            parent = rec.declaration_id or rec.table_period_id
            if (
                not parent
                or rec.event_type not in OPERABLE_EVENT_TYPES
                or parent._active_event(rec.event_type).id != rec.id
            ):
                continue
            if rec.declaration_id:
                allowed = {
                    EVENT_D1101: rec.declaration_id.can_replace_trial,
                    EVENT_D1106: rec.declaration_id.can_replace_d1106,
                    EVENT_D1121: rec.declaration_id.can_replace_d1121,
                }
                rec.can_replace_event = allowed.get(rec.event_type, False)
                rec.can_exclude_event = rec.can_replace_event
                rec.can_rectify_event = (
                    rec.event_type == EVENT_D1121
                    and rec.declaration_id.can_rectify_d1121
                )
                continue
            rec.can_replace_event = parent._can_replace_or_exclude(rec.event_type)
            rec.can_exclude_event = rec.can_replace_event

    def action_replace_event(self):
        self.ensure_one()
        if not self.can_replace_event:
            raise UserError(_("This event cannot be replaced."))
        if self.table_period_id:
            return self._open_operation_wizard("2")
        generators = {
            EVENT_D1101: self.declaration_id._generate_d1101,
            EVENT_D1106: self.declaration_id._generate_d1106,
            EVENT_D1121: self.declaration_id._generate_d1121,
        }
        method = generators.get(self.event_type)
        if not method:
            raise UserError(_("This event cannot be replaced."))
        method(tp_oper="2")
        return True

    def action_exclude_event(self):
        self.ensure_one()
        if not self.can_exclude_event:
            raise UserError(_("This event cannot be excluded."))
        return self._open_operation_wizard("3")

    def action_rectify_event(self):
        self.ensure_one()
        if not self.can_rectify_event:
            raise UserError(_("This event cannot be rectified."))
        return self._open_operation_wizard("4")

    def _open_operation_wizard(self, tp_oper):
        self.ensure_one()
        period = self.table_period_id
        wizard = self.env["l10n_br_dere.event.operation.wizard"].create(
            {
                "declaration_id": self.declaration_id.id,
                "table_period_id": period.id,
                "event_type": self.event_type,
                "tp_oper": tp_oper,
                "nova_ini_valid": period.ini_valid if period else False,
                "nova_fim_valid": period.fim_valid if period else False,
                "fin_evt": "1" if tp_oper == "4" else False,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("DeRE event operation"),
            "res_model": "l10n_br_dere.event.operation.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.depends(
        "event_type",
        "declaration_id.per_apur",
        "table_period_id.ini_valid",
    )
    def _compute_name(self):
        for rec in self:
            period = rec.declaration_id.per_apur or rec.table_period_id.ini_valid or ""
            rec.name = f"{rec.event_type or ''} {period}"

    @api.constrains("tp_oper", "event_type")
    def _check_tp_oper(self):
        allowed = {
            EVENT_D1198: {"1"},
            EVENT_D1199: {"1"},
            EVENT_D1121: {"1", "2", "3", "4"},
        }
        for rec in self:
            values = allowed.get(rec.event_type, {"1", "2", "3"})
            if rec.tp_oper not in values:
                raise ValidationError(
                    _("Event %(event_type)s does not admit tpOper %(tp_oper)s.")
                    % {"event_type": rec.event_type, "tp_oper": rec.tp_oper}
                )

    _event_id_seq = {}

    @api.model
    def _next_event_id_seq(self, timestamp):
        last = self._event_id_seq.get(timestamp, 0) + 1
        if last > 99999:
            raise UserError(
                _("Too many DeRE events were generated in the same second.")
            )
        self._event_id_seq[timestamp] = last
        return f"{last:05d}"

    @api.model
    def _generate_event_id(self, event_type=None, company=None, tp_amb=None):
        if self and not event_type:
            event_type = self.event_type
            company = company or self.company_id
        if event_type not in STRUCTURED_EVENT_ID:
            # loteEventos/@id is xs:ID, so the value must start with a letter.
            return ("A" + uuid.uuid4().hex)[:42].ljust(42, "0")
        code = event_type.replace("D-", "")
        root = (company._dere_cnpj_root() if company else "").upper()
        if not re.fullmatch(r"[0-9A-Z]{8}", root):
            raise UserError(_("Set a valid 8-character CNPJ root on the company."))
        inscription = root.rjust(14, "0")
        now = datetime.now(ZoneInfo(BRASILIA_TZ))
        timestamp = now.strftime("%Y%m%d%H%M%S")
        return (
            f"DeRE{code}{EVENT_ID_INSCRIPTION_TYPE}{inscription}"
            f"{timestamp}{self._next_event_id_seq(timestamp)}"
        )

    def _format_xsd_errors(self, errors):
        return "\n".join(errors[:8])

    def _assert_valid_xml(self, xml, signed=False):
        self.ensure_one()
        if self.event_type not in xsd_validator.EVENT_SCHEMA:
            return True
        errors = xsd_validator.validate(xml, self.event_type, signed=signed)
        if errors:
            raise UserError(
                _("DeRE %(event)s XML failed official XSD validation:\n%(errors)s")
                % {
                    "event": self.event_type,
                    "errors": self._format_xsd_errors(errors),
                }
            )
        return True

    @api.model
    def _return_payload_vals(self, payload):
        if not payload:
            return {}
        return {
            "return_type": RETURN_TYPE_BY_TAG.get(payload.get("returnTag"), False),
            "return_xml": payload.get("xml") or False,
            "seq_evento": payload.get("seqEvento") or False,
            "dh_recepcao": xml_builder.parse_datetime(payload.get("dhRecepcao")),
            "dh_process": xml_builder.parse_datetime(payload.get("dhProcess")),
            "nr_recibo_pgcc": payload.get("nrReciboPGCC") or False,
        }

    def _return_parent(self):
        self.ensure_one()
        return self.declaration_id or self.table_period_id

    def _check_return_schema(self):
        for rec in self.filtered("return_xml"):
            errors = xsd_validator.validate_return(rec.return_xml)
            if not errors:
                continue
            rec.message_post(
                body=Markup("%s<br/>%s")
                % (
                    _("The return XML does not match its official XSD:"),
                    Markup("<br/>").join(errors[:8]),
                )
            )

    def _store_xml(self, xml):
        self.ensure_one()
        self._assert_valid_xml(xml, signed=False)
        digest = hashlib.sha256(xml.encode("utf-8")).hexdigest()
        self.write(
            {
                "xml_content": xml,
                "xml_hash": digest,
                "event_id_attr": self.event_id_attr or self._generate_event_id(),
                "state": "generated",
            }
        )
        return xml


class DereEventOccurrence(models.Model):
    _name = "l10n_br_dere.event.occurrence"
    _description = "DeRE event occurrence"

    event_id = fields.Many2one(
        comodel_name="l10n_br_dere.event", required=True, ondelete="cascade"
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="event_id.company_id",
        store=True,
        index=True,
    )
    codigo = fields.Char(string="Code", required=True, size=6)
    descricao = fields.Char(string="Description", required=True)
    tipo = fields.Selection(
        [("1", "Error"), ("2", "Warning")],
        string="Type",
        required=True,
    )
    localizacao = fields.Char(string="Location")
