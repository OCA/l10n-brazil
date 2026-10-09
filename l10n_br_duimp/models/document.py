# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    duimp_number = fields.Char(
        string="DUIMP Number",
        copy=False,
        help="Number of the DUIMP (Import Declaration) that originated "
        "this fiscal document.",
    )

    duimp_version = fields.Integer(
        string="DUIMP Version",
        copy=False,
    )
