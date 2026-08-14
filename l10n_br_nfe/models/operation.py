# Copyright (C) 2026 KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.nfe import NFE_PAYMENT_TYPES


class Operation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    nfe_payment_type = fields.Selection(
        selection=NFE_PAYMENT_TYPES,
        string="NFe Payment Type",
        help=(
            "Payment type (tPag) used to fill the payment group of a NF-e "
            "issued under this operation. Empty falls back to the company "
            "default."
        ),
    )
