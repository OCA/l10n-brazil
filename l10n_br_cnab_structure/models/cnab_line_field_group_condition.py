# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class CNABFieldCondition(models.Model):
    """
    Model to store the condition of a field
    """

    _name = "cnab.line.group.field.condition"
    _description = "Cnab Field Condition"

    @api.model
    def default_get(self, fields_list):
        """Override default_get"""
        res = super().default_get(fields_list)
        # It seems to be a bug in native odoo that the field cnab_line_id
        # is not in the fields list by default. A workaround is required
        # to force this.
        if (
            "default_cnab_group_id" in self._context
            and "cnab_group_id" not in fields_list
        ):
            fields_list.append("cnab_group_id")
            res["cnab_group_id"] = self._context.get("default_cnab_group_id")
        return res

    cnab_group_id = fields.Many2one(
        comodel_name="cnab.line.field.group",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    cnab_line_id = fields.Many2one(
        comodel_name="l10n_br_cnab.line", related="cnab_group_id.cnab_line_id"
    )

    field_id = fields.Many2one(
        comodel_name="l10n_br_cnab.line.field",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('cnab_line_id', '=', cnab_line_id)]",
    )

    operator = fields.Selection(
        selection=[("in", "in"), ("not in", "not in")],
        required=True,
        default="in",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    json_value = fields.Char(
        string="Value (JSON format)",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    state = fields.Selection(
        readonly=True,
        related="cnab_group_id.state",
    )
