# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CNABBatch(models.Model):

    _name = "l10n_br_cnab.batch"
    _description = "A batch of lines in a CNAB file."

    name = fields.Char(readonly=True, states={"draft": [("readonly", "=", False)]})

    cnab_file_id = fields.Many2one(
        comodel_name="l10n_br_cnab.file",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
        domain="[('cnab_format', '=', '240')]",
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_cnab.line",
        inverse_name="batch_id",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
        domain="[('cnab_format', '=', '240')]",
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("review", "Review"), ("approved", "Approved")],
        readonly=True,
        default="draft",
    )

    def unlink(self):
        lines = self.filtered(lambda l: l.state != "draft")
        if lines:
            raise UserError(_("You cannot delete an CNAB Batch which is not draft !"))
        return super(CNABBatch, self).unlink()

    def check_batch(self):
        for l in self.line_ids:
            l.check_line()
