# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants.nfse_nacional import NFSE_NACIONAL_BENEFIT_TYPES


class CityTaxationCode(models.Model):
    _inherit = "l10n_br_fiscal.city.taxation.code"

    nfse_benefit_code = fields.Char(
        string="Municipal Benefit (nBM)",
        size=14,
        help="Identifier of the municipal benefit registered by the city in the "
        "national NFS-e system, declared in the BM group of the DPS.",
    )
    nfse_benefit_type = fields.Selection(
        NFSE_NACIONAL_BENEFIT_TYPES,
        string="Municipal Benefit Type",
    )
