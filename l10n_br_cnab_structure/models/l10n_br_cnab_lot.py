# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class CNABReturnLot(models.Model):
    """Override CNAB Return Lot"""

    _inherit = "l10n_br_cnab.return.lot"
    _rec_name = "seq_number"

    seq_number = fields.Char()
