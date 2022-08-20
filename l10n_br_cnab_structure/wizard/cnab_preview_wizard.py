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

    payment_order_id = fields.Many2one(
        comodel_name="account.payment.order",
        string="Payment Order",
    )

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
    )

    output = fields.Text(string="CNAB Text Output")

    cnab_file = fields.Binary(
        string="CNAB File",
    )

    cnab_file_name = fields.Char(compute="_compute_cnab_file_name")

    @api.onchange("payment_order_id")
    def _onchange_payment_order_id(self):
        self._compute_cnab_txt()

    def _compute_cnab_file_name(self):
        for rec in self:
            file_name = f"CNAB_TEST_{rec.payment_order_id.name}.REM"
            rec.cnab_file_name = file_name

    @api.depends("cnab_structure_id", "payment_order_id")
    def _compute_cnab_txt(self):
        txt = ""
        if self.payment_order_id:
            txt = self.cnab_structure_id.output(self.payment_order_id)
        self.output = txt
        file = txt.encode("utf-8")
        self.cnab_file = base64.b64encode(file)

    def load_file(self):
        """Action for download CNAB File"""
        return {
            "name": "CNAB",
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model=cnab.preview.wizard&id={self.id}&field=cnab_file"
            "&filename_field=cnab_file_name&download=true",
            "target": "self",
        }
