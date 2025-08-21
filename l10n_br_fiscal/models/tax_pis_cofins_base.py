# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class TaxPisCofinsBase(models.Model):
    _name = "l10n_br_fiscal.tax.pis.cofins.base"
    _inherit = "l10n_br_fiscal.data.abstract"
    _description = "Tax PIS/COFINS Base"

    code = fields.Char(size=2)

    _sql_constraints = [
        (
            "code_unique",
            "unique (code)",
            "Already exists with this code!",
        )
    ]
