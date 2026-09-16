# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import TP_AMB

_logger = logging.getLogger(__name__)

CRON_CONSULT_LIMIT = 50


class DereBatch(models.Model):
    _name = "l10n_br_dere.batch"
    _description = "DeRE transmission batch"
    _order = "id desc"

    name = fields.Char(required=True, default="New")
    declaration_id = fields.Many2one(
        comodel_name="l10n_br_dere.declaration",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="declaration_id.company_id", store=True)
    tp_amb = fields.Selection(TP_AMB, string="Environment", required=True)
    event_ids = fields.Many2many(comodel_name="l10n_br_dere.event", string="Events")
    xml_content = fields.Text(string="XML")
    protocol = fields.Char(string="Batch protocol", size=28)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="draft",
        required=True,
    )
    response_text = fields.Text(string="Response")

    def action_consult(self):
        for batch in self:
            batch._consult(raise_error=True)
        return True

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
            _logger.warning(
                "DeRE consult skipped for batch %s (%s)",
                self.id,
                self.protocol,
                exc_info=True,
            )
            if raise_error:
                raise
            return False
        self.response_text = result["text"]
        if not result["ok"]:
            if raise_error:
                self.state = "error"
                raise UserError(
                    _("Receita Integra rejected the batch query: %s") % result["text"]
                )
            _logger.warning(
                "DeRE consult HTTP %s for batch %s: %s",
                result["status_code"],
                self.id,
                result["text"],
            )
            return False
        self.declaration_id._apply_consult_result(self, result["text"])
        return True

    @api.model
    def _cron_consult_batches(self):
        batches = self.search(
            [("state", "=", "sent"), ("protocol", "!=", False)],
            limit=CRON_CONSULT_LIMIT,
            order="id",
        )
        for batch in batches:
            try:
                batch._consult(raise_error=False)
            except Exception:
                _logger.exception("DeRE consult cron failed for batch %s", batch.id)
        return True
