# Copyright 2025 Engenere.one
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Uom(models.Model):
    _inherit = "uom.uom"

    code = fields.Char(
        size=6,
        translate=False,
        help="Abbreviated unit code used in electronic fiscal documents "
        "(e.g. NF-e, NFC-e). Must have a maximum of 6 characters "
        "by regulation. e.g. 'UN', 'KG', 'LITRO', 'CX12UN",
    )

    description = fields.Char(
        help="Full unit description. e.g. 'Unit', 'Kilogram', 'Box of 12 Units'.",
    )

    _sql_constraints = [
        ("unique_code", "UNIQUE(code)", "Unit of Measure code must be unique!")
    ]
