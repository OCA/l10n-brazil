# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import TP_AMB

_logger = logging.getLogger(__name__)

CRON_CONSULT_LIMIT = 50
CONSULT_BACKOFF_MINUTES = (2, 4, 8, 16, 32, 60)


class DereBatch(models.Model):
    _name = "l10n_br_dere.batch"
    _description = "DeRE transmission batch"
    _order = "id desc"

    name = fields.Char(required=True, default="New")
    declaration_id = fields.Many2one(
        comodel_name="l10n_br_dere.declaration",
        ondelete="cascade",
    )
    table_period_id = fields.Many2one(
        comodel_name="l10n_br_dere.table.period",
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        compute="_compute_company_id",
        store=True,
        index=True,
    )
    tp_amb = fields.Selection(TP_AMB, string="Environment", required=True)
    event_ids = fields.Many2many(comodel_name="l10n_br_dere.event", string="Events")
    xml_content = fields.Text(string="XML")
    protocol = fields.Char(string="Batch protocol", size=28)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("unknown", "Unknown"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="draft",
        required=True,
    )
    response_text = fields.Text(string="Response")
    consult_attempts = fields.Integer(default=0)
    next_consult_at = fields.Datetime(string="Next consult")

    @api.depends("declaration_id.company_id", "table_period_id.company_id")
    def _compute_company_id(self):
        for rec in self:
            rec.company_id = (
                rec.declaration_id.company_id or rec.table_period_id.company_id
            )

    def _schedule_next_consult(self, processed=False):
        self.ensure_one()
        if processed:
            self.next_consult_at = False
            return
        index = min(self.consult_attempts, len(CONSULT_BACKOFF_MINUTES) - 1)
        delay = CONSULT_BACKOFF_MINUTES[index]
        self.consult_attempts += 1
        self.next_consult_at = fields.Datetime.now() + timedelta(minutes=delay)

    def action_consult(self):
        for batch in self:
            batch._consult(raise_error=True)
        return True

    def _parent_record(self):
        self.ensure_one()
        return self.declaration_id or self.table_period_id

    def _consult(self, raise_error=True):
        self.ensure_one()
        if not self.protocol:
            if raise_error:
                raise UserError(_("Batch %s has no protocol to consult.") % self.name)
            return False
        try:
            result = self.env["l10n_br_dere.receita.integra"].consult_batch(
                self.company_id, self.protocol
            )
        except UserError:
            _logger.info(
                "DeRE consult skipped for batch %s (%s)",
                self.id,
                self.protocol,
                exc_info=True,
            )
            if raise_error:
                raise
            self._schedule_next_consult()
            return False
        self.response_text = result["text"]
        if not result["ok"]:
            if raise_error:
                self.state = "error"
                raise UserError(
                    _("Receita Integra rejected the batch query: %s") % result["text"]
                )
            _logger.info(
                "DeRE consult HTTP %s for batch %s: %s",
                result["status_code"],
                self.id,
                result["text"],
            )
            self._schedule_next_consult()
            return False
        parent = self._parent_record()
        applied = (
            parent._apply_consult_result(self, result["text"]) if parent else False
        )
        if self.state == "sent":
            self._schedule_next_consult()
        else:
            self._schedule_next_consult(processed=True)
        return applied

    @api.model
    def _cron_consult_batches(self):
        now = fields.Datetime.now()
        batches = self.search(
            [
                ("state", "=", "sent"),
                ("protocol", "!=", False),
                "|",
                ("next_consult_at", "=", False),
                ("next_consult_at", "<=", now),
            ],
            limit=CRON_CONSULT_LIMIT,
            order="id",
        )
        for batch in batches:
            try:
                batch._consult(raise_error=False)
            except Exception:
                _logger.exception("DeRE consult cron failed for batch %s", batch.id)
        return True
