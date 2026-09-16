# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import re
import secrets
import uuid
from datetime import datetime, timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import (
    APLIC_EMI,
    CD_RETORNO,
    MOT_EXCL,
    TP_AMB,
    TP_OPER,
)

from ..constants import EVENT_TYPES, STRUCTURED_EVENT_ID


class DereEvent(models.Model):
    _name = "l10n_br_dere.event"
    _description = "DeRE event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(compute="_compute_name", store=True)
    declaration_id = fields.Many2one(
        comodel_name="l10n_br_dere.declaration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="declaration_id.company_id", store=True)
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
        TP_OPER, string="Operation type", default="1", required=True
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

    @api.depends("event_type", "declaration_id.per_apur")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.event_type or ''} {rec.declaration_id.per_apur or ''}"

    @api.model
    def _generate_event_id(self, event_type=None, company=None, tp_amb=None):
        if self and not event_type:
            event_type = self.event_type
            company = company or self.company_id
            tp_amb = tp_amb or self.tp_amb
        if event_type not in STRUCTURED_EVENT_ID:
            return uuid.uuid4().hex[:42].ljust(42, "0")
        code = event_type.replace("D-", "")
        environment = str(tp_amb or (company.dere_tp_amb if company else "2") or "2")
        if environment not in ("1", "2"):
            environment = "2"
        cnpj = (company._dere_cnpj() if company else "").upper()
        if not re.fullmatch(r"[0-9A-Z]{14}", cnpj):
            raise UserError(_("Set a valid 14-character CNPJ on the company."))
        seq = (
            f"{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
            f"{secrets.randbelow(100000):05d}"
        )
        return f"DeRE{code}{environment}{cnpj}{seq}"

    def _store_xml(self, xml):
        self.ensure_one()
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
    codigo = fields.Char(string="Code", required=True, size=6)
    descricao = fields.Char(string="Description", required=True)
    tipo = fields.Selection(
        [("1", "Error"), ("2", "Warning")],
        string="Type",
        required=True,
    )
    localizacao = fields.Char(string="Location")
