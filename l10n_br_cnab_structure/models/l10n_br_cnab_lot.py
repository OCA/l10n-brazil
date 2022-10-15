# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class CNABReturnLot(models.Model):
    """Override CNAB Return Lot"""

    _inherit = "l10n_br_cnab.return.lot"
    _rec_name = "seq_number"

    seq_number = fields.Char()
