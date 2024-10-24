from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cte_authorize_accountant_download_xml = fields.Boolean(
        string="Include Accountant Partner data in persons authorized to "
        "download CTe XML",
        related="company_id.cte_authorize_accountant_download_xml",
        readonly=False,
    )
