# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import TP_AMB


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
            if not batch.protocol:
                raise UserError(_("Batch %s has no protocol to consult.") % batch.name)
            result = self.env["l10n_br_dere.receita.integra"].consult_batch(
                batch.company_id, batch.protocol
            )
            batch.response_text = result["text"]
            if not result["ok"]:
                batch.state = "error"
                raise UserError(
                    _("Receita Integra rejected the batch query: %s") % result["text"]
                )
            batch.declaration_id._apply_consult_result(batch, result["text"])
        return True
