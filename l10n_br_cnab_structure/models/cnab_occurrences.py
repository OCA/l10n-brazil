# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class CNABOccurrences(models.Model):
    """CNAB Occurrences Code"""

    _name = "cnab.occurrence"
    _description = "CNAB Occurence Code"

    name = fields.Char(compute="_compute_name")
    code = fields.Char(required=True)
    description = fields.Char()

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        string="Cnab Structure",
        ondelete="cascade",
        required=True,
    )

    gen_liquidation_move = fields.Boolean(
        string="Generate Liquidation Move",
        help="Mark this option if this occurrence corresponds to a liquidation move.",
    )

    @api.depends("code", "name")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.code} - {rec.description}"
