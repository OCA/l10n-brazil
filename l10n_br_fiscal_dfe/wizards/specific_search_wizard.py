import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DfeSpecificSearchWizard(models.TransientModel):
    _name = "dfe.specific.search.wizard"
    _description = "Specific DF-e Search"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    fiscal_type = fields.Selection([("nfe", "NF-e"), ("cte", "CT-e")], required=True)
    search_type = fields.Selection(
        [("access_key", "Access Key"), ("nsu", "NSU")],
        default="access_key",
        required=True,
    )
    access_key = fields.Char()
    nsu = fields.Char(string="NSU")

    @api.onchange("access_key")
    def _onchange_access_key(self):
        if self.access_key:
            self.access_key = re.sub("[^0-9]", "", self.access_key)

    def action_confirm_search(self):
        self.ensure_one()
        if self.search_type == "access_key":
            if not self.access_key or len(self.access_key) != 44:
                raise UserError(
                    _("Invalid access key. It must contain exactly 44 digits.")
                )
        else:
            if not self.nsu or not self.nsu.isdigit() or int(self.nsu) == 0:
                raise UserError(_("Invalid NSU."))

        # Delegate to the specific Sefaz client based on document type
        if self.fiscal_type == "nfe":
            self.company_id._nfe_dfe_search_specific_document(
                access_key=self.access_key, nsu=self.nsu
            )
        else:
            self.company_id._cte_dfe_search_specific_document(
                access_key=self.access_key, nsu=self.nsu
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": _(
                    "Search sent successfully. Please check the logs or documents list."
                ),
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }
