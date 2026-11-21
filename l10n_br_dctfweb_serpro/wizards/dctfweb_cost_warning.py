# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

from ..constants import SERVICES


class DctfwebCostWarning(models.TransientModel):
    """Ask before spending money.

    The Integra Contador bills per request, so a mistyped period costs real
    money. The warning is what turns a billed call into a deliberate act, and
    a company that does not want it turns it off once.
    """

    _name = "l10n_br_dctfweb.cost.warning"
    _description = "DCTFWeb billed call warning"

    assessment_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.assessment",
        required=True,
        readonly=True,
    )
    service_key = fields.Char(required=True, readonly=True)
    service_name = fields.Char(compute="_compute_service_name")
    billed_count = fields.Integer(
        compute="_compute_service_name",
        string="Billed calls already made",
    )

    @api.depends("service_key", "assessment_id")
    def _compute_service_name(self):
        for record in self:
            service = SERVICES.get(record.service_key or "", {})
            record.service_name = service.get("name") or record.service_key
            record.billed_count = len(
                record.assessment_id.transmission_ids.filtered("billed")
            )

    def action_confirm(self):
        self.ensure_one()
        return self.assessment_id.run_service(self.service_key)

    def action_never_warn_again(self):
        """Turn the warning off for the company and run the call."""
        self.ensure_one()
        self.assessment_id.company_id.sudo().serpro_warn_cost = False
        return self.action_confirm()
