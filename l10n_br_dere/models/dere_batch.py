# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

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
