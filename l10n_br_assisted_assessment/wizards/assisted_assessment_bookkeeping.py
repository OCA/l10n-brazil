# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants import BOOKKEEPING_STATUSES, LINE_TYPES


class AssistedAssessmentBookkeepingLine(models.TransientModel):
    _name = "l10n_br_assessment.bookkeeping.line"
    _description = "ERP document expected in the assisted assessment"
    _order = "line_type, document_key, id"

    period_id = fields.Many2one(
        comodel_name="l10n_br_assessment.period",
        required=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="period_id.company_id")
    currency_id = fields.Many2one(related="period_id.currency_id")
    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        required=True,
    )
    document_key = fields.Char(related="document_id.document_key")
    line_type = fields.Selection(selection=LINE_TYPES, required=True)
    expected_value = fields.Monetary(
        help="CBS or IBS booked on the authorized fiscal document.",
    )
    fisco_value = fields.Monetary(string="Assessed Value")
    status = fields.Selection(selection=BOOKKEEPING_STATUSES, required=True)
