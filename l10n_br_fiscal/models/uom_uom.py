# Copyright 2025 Engenere.one
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Uom(models.Model):
    _inherit = "uom.uom"

    @api.model
    def _match_by_fiscal_code(self, *codes):
        """Match a UoM from one or more fiscal unit codes (e.g. the uCom /
        uTrib of an imported document).

        First try the fiscal ``code`` field, then fall back to the
        ``uom_alias`` module aliases so that supplier abbreviations
        (e.g. ``MIL`` -> ``MILHEIRO``, ``UNID`` -> ``Units``) resolve to
        the company's own UoM.
        """
        codes = [code for code in codes if code]
        if not codes:
            return self.browse()
        uom = self.search([("code", "in", codes)], limit=1)
        if not uom:
            uom = self.search([("alias_ids.code", "in", codes)], limit=1)
        return uom

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
