# Copyright (C) 2020  Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BaseWizardMixin(models.TransientModel):
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice",
    )

    @api.model
    def default_get(self, fields_list):
        default_values = super().default_get(fields_list)
        if default_values.get("move_id"):
            move_id = self.move_id.browse(default_values.get("move_id"))
            default_values["document_id"] = move_id.fiscal_document_id.id
        return default_values

    def _prepare_key_fields(self):
        vals = super()._prepare_key_fields()
        vals["account.move"] = "move_id"
        return vals
