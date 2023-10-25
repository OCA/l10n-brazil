# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class CNABFieldGroup(models.Model):
    """
    Model for defining rules for a group of fields within a cnab line.
    """

    _name = "cnab.line.field.group"
    _description = "Cnab Field Group"

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # It seems to be a bug in native odoo that the field cnab_line_id
        # is not in the fields list by default. A workaround is required
        # to force this.
        if "default_cnab_line_id" in self._context and "cnab_line_id" not in fields:
            fields.append("cnab_line_id")
            res["cnab_line_id"] = self._context.get("default_cnab_line_id")
        return res

    name = fields.Char(states={"draft": [("readonly", False)]})

    cnab_line_id = fields.Many2one(
        "l10n_br_cnab.line",
        ondelete="cascade",
        required=True,
        states={"draft": [("readonly", False)]},
    )

    field_ids = fields.One2many(
        comodel_name="l10n_br_cnab.line.field",
        inverse_name="cnab_group_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('cnab_line_id', '=', cnab_line_id)]",
    )

    condition_ids = fields.One2many(
        comodel_name="cnab.line.group.field.condition",
        inverse_name="cnab_group_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    state = fields.Selection(
        readonly=True,
        related="cnab_line_id.state",
    )
