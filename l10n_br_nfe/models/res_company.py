# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.nfe import (NFE_ENVIRONMENT_DEFAULT, NFE_ENVIRONMENTS,
                             NFE_VERSION_DEFAULT, NFE_VERSIONS)


class ResCompany(models.Model):
    _inherit = "res.company"

    nfe_version = fields.Selection(
        selection=NFE_VERSIONS, string="NFe Version", default=NFE_VERSION_DEFAULT
    )

    nfe_environment = fields.Selection(
        selection=NFE_ENVIRONMENTS,
        string="NFe Environment",
        default=NFE_ENVIRONMENT_DEFAULT,
    )

    nfe_default_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie", string="NF-e Default Serie"
    )
