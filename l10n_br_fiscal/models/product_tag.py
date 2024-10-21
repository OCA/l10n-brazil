# Copyright (C) 2024  Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class ProductTag(models.Model):
    _name = "l10n_br_fiscal.product.tag"
    _description = "Fiscal Product Tags"

    name = fields.Char()

    _sql_constraints = [
        (
            "fiscal_tag_name_uniq",
            "unique (name)",
            _("Fiscal Product Tag already exists with this code !"),
        )
    ]
