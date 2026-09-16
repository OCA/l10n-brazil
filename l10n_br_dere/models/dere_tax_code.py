# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DereTaxCode(models.Model):
    _name = "l10n_br_dere.tax.code"
    _description = "DeRE taxation code (codTrib)"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=9)
    legal_ref = fields.Char(string="Legal reference")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_uniq", "unique(code)", "The taxation code must be unique."),
    ]
