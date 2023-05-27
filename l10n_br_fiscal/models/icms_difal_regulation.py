# Copyright (C) 2023  Felipe Motter Pereira - Akretion <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ICMSDifalRegulation(models.Model):
    _name = "l10n_br_fiscal.icms.difal.regulation"
    _description = "ICMS Difal Regulation"

    name = fields.Text(required=True, index=True)

    unique_base_state_ids = fields.Many2many(
        comodel_name="res.country.state",
        relation="icms_difal_regulation_unique_base_state_rel",
        column1="icms_difal_regulation",
        column2="state_id",
        string="States with Unique Base",
        domain=[("country_id.code", "=", "BR")],
    )

    double_base_state_ids = fields.Many2many(
        comodel_name="res.country.state",
        relation="icms_difal_regulation_double_base_state_rel",
        column1="icms_difal_regulation",
        column2="state_id",
        string="States with Double Base",
        domain=[("country_id.code", "=", "BR")],
    )

    @api.constrains("unique_base_state_ids", "double_base_state_ids")
    def _check_duplicity(self):
        for state in self.unique_base_state_ids:
            if state in self.double_base_state_ids:
                raise UserError(_("You cannot have two bases for same state."))
        return True
