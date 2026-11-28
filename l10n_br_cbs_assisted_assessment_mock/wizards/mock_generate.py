# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_assisted_assessment.constants import (
    SERVICE_CREDITS,
    SERVICE_DEBITS,
    SERVICE_PAYMENTS,
    SERVICE_WITHHOLDINGS,
    TRIBUTE_CBS,
)


class CbsAssessmentMockGenerate(models.TransientModel):
    _name = "l10n_br_cbs_assisted_assessment.mock.generate"
    _description = "Prepare local CBS assessment files"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    period_id = fields.Many2one(
        comodel_name="l10n_br_assisted_assessment.period",
        required=True,
        domain="[('company_id', '=', company_id), ('tribute', '=', 'cbs')]",
    )
    debits = fields.Boolean(default=True)
    credits = fields.Boolean(default=True)
    payments = fields.Boolean(default=True)
    withholdings = fields.Boolean(string="Acquirer Withholdings", default=True)

    def action_generate(self):
        self.ensure_one()
        if self.period_id.tribute != TRIBUTE_CBS:
            raise UserError(_("Choose a CBS assessment period."))
        services = []
        if self.debits:
            services.append(SERVICE_DEBITS)
        if self.credits:
            services.append(SERVICE_CREDITS)
        if self.payments:
            services.append(SERVICE_PAYMENTS)
        if self.withholdings:
            services.append(SERVICE_WITHHOLDINGS)
        if not services:
            raise UserError(_("Select at least one service to prepare."))
        files = self.env["l10n_br_cbs_assisted_assessment.mock.file"]._prepare(
            self.period_id, services
        )
        return {
            "type": "ir.actions.act_window",
            "name": "CBS Mock Files",
            "res_model": "l10n_br_cbs_assisted_assessment.mock.file",
            "view_mode": "list,form",
            "domain": [("id", "in", files.ids)],
            "target": "current",
        }
