# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import REG_TRIB_SECUND


class DereTaxAssessmentLine(models.Model):
    _name = "l10n_br_dere.tax.assessment.line"
    _description = "DeRE IBS/CBS base assessed by the RFB"
    _inherit = "dere.12.detbc"
    _order = "regime, dere12_codBC, id"

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_dere.declaration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    event_id = fields.Many2one(
        comodel_name="l10n_br_dere.event",
        string="D-1199 event",
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="declaration_id.company_id", store=True)
    regime = fields.Selection(REG_TRIB_SECUND, string="Specific regime", required=True)
