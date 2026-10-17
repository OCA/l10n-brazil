# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_is_zero


class DereEventTotal(models.Model):
    _name = "l10n_br_dere.event.total"
    _description = "DeRE assessed total returned by the RFB"
    _inherit = "dere.12.gtotalcodtrib"
    _order = "event_id, dere12_codTrib, dere12_indTribISS"

    event_id = fields.Many2one(
        comodel_name="l10n_br_dere.event",
        required=True,
        ondelete="cascade",
        index=True,
    )
    event_type = fields.Selection(related="event_id.event_type", store=True)
    company_id = fields.Many2one(related="event_id.company_id", store=True)
    local_v_apur = fields.Monetary(
        string="Local assessed total",
        currency_field="brl_currency_id",
        help="Sum of the vApur sent in the event for this taxation code.",
    )
    difference = fields.Monetary(
        compute="_compute_difference",
        store=True,
        currency_field="brl_currency_id",
    )
    has_difference = fields.Boolean(compute="_compute_difference", store=True)

    @api.depends("dere12_vApurTot", "local_v_apur")
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.dere12_vApurTot - rec.local_v_apur
            rec.has_difference = not float_is_zero(rec.difference, precision_digits=2)
