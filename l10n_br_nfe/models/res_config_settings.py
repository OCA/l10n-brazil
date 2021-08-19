# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.nfe import NFE_ENVIRONMENTS, NFE_VERSIONS, NFE_TRANSMISSIONS


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    nfe_version = fields.Selection(
        string="NF-e Version",
        selection=NFE_VERSIONS,
        related="company_id.nfe_version",
        readonly=False,
    )

    nfe_environment = fields.Selection(
        string="NFe Environment",
        selection=NFE_ENVIRONMENTS,
        related="company_id.nfe_environment",
        readonly=False,
    )

    nfe_transmission = fields.Selection(
        string="NFe Transmission",
        selection=NFE_TRANSMISSIONS,
        related="company_id.nfe_transmission",
        readonly=False,
    )


NFE_TRANSMISSIONS
