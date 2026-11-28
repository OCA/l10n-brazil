# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CNABStructure(models.Model):
    _inherit = "l10n_br_cnab.structure"

    is_dda_return = fields.Boolean(
        string="DDA return",
        help="The file of this structure lists the boletos registered against "
        "the CNPJ of the company (DDA). It is read by the DDA import, not by the "
        "return of collection.",
    )
