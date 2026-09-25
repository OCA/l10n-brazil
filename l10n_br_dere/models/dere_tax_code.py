# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class DereTaxCode(models.Model):
    _name = "l10n_br_dere.tax.code"
    _description = "DeRE taxation code (codTrib)"
    _rec_names_search = ["code", "name"]

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=9)
    description = fields.Text(
        help="Official table 11 text that explains what to classify under this code.",
    )
    legal_ref = fields.Char(string="Legal reference")
    active = fields.Boolean(default=True)

    @api.depends("code", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = " - ".join(filter(None, [rec.code, rec.name]))

    _sql_constraints = [
        ("code_uniq", "unique(code)", "The taxation code must be unique."),
    ]
