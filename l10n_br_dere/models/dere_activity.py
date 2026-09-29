# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DereActivity(models.Model):
    _name = "l10n_br_dere.activity"
    _description = "DeRE activity code"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=3)
    table_code = fields.Selection(
        [
            ("21", "Table 21 - Financial services"),
            ("31", "Table 31 - Health-care plans"),
            ("41", "Table 41 - Prize contests"),
        ],
        required=True,
        default="31",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "code_table_uniq",
            "unique(code, table_code)",
            "The activity code must be unique per official table.",
        )
    ]
