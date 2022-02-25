from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    fiscal_dummy_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        required=True,
    )
