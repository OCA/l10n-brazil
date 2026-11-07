# Copyright (C) 2024-Today - KMEE (<https://kmee.com.br>)
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    siscomex_code = fields.Char(
        help="Numeric currency code used by the Portal Único Siscomex "
        "(DI/DUIMP), which does not use the ISO alphabetic code.",
    )
