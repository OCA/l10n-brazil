# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
from odoo import _, api, fields, models


class CNABPreviewWizard(models.TransientModel):

    _name = "cnab.preview.wizard"
    _description = "CNAB Preview Wizard"

    @api.model
    def _selection_target_model(self):
        return [
            ("account.payment.order", "Payment Order"),
            ("bank.payment.line", "Bank Payment Line"),
        ]

    resource_ref = fields.Reference(
        string="Reference",
        selection="_selection_target_model",
    )

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.file",
    )

    output = fields.Text(string="CNAB Text Output", compute="_compute_cnab_txt")

    cnab_file_txt = fields.Binary()

    @api.depends("cnab_structure_id", "resource_ref")
    def _compute_cnab_txt(self):
        txt = ""
        if self.resource_ref:
            txt = self.cnab_structure_id.output(self.resource_ref)
        self.output = txt

        file = txt.encode("utf-8")
        self.cnab_file_txt = base64.b64encode(file)
